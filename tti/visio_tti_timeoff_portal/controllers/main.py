import base64
import logging
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import date
_logger = logging.getLogger(__name__)


class TimeOffController(http.Controller):

    @http.route('/my/timeoffs', type='http', auth="user", website=True)
    def timeoffs(self, **kwargs):
        employee = request.env.user.employee_id
        user = request.env.user
        if not employee:
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            _logger.info("[employee orm ] user=%s", employee and employee.id)
        # if not employee:
        #     return request.redirect('/')
        print("leave manager", employee.leave_manager_id)

        # Check if user is a manager of any employees
        subordinates = request.env['hr.employee'].sudo().search([('parent_id.user_id', '=', request.env.user.id)])
        is_manager = bool(subordinates)

        subordinate_emps = request.env['hr.employee'].sudo().search([
            ('hr.user_id', '=', request.env.user.id)
        ])
        is_hr = bool(subordinate_emps)

        current_date = fields.Date.today()
        year_start = fields.Date.to_string(fields.Date.from_string(f"{current_date.year}-01-01"))
        year_end = fields.Date.to_string(fields.Date.from_string(f"{current_date.year}-12-31"))

        # Get allocations that are portal-enabled only (excluding Compensatory Days)
        allocations = request.env['hr.leave.allocation'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('holiday_status_id.is_portal', '=', True),
            ('holiday_status_id.name', '!=', 'Compensatory Days'),
            '|',
            ('date_from', '<=', year_end),
            ('date_from', '=', False),
            '|',
            ('date_to', '>=', year_start),
            ('date_to', '=', False),
        ])

        # Calculate allocation data with real-time usage
        allocation_data = []
        current_date = fields.Date.today()

        for allocation in allocations:
            leave_type = allocation.holiday_status_id

            # Build domain for leaves used in this allocation period
            leave_domain = [
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', leave_type.id),
                ('state', 'not in', ['refuse', 'cancel']),
            ]

            # Only consider leaves within allocation's dates
            if allocation.date_from:
                leave_domain.append(('request_date_from', '>=', allocation.date_from))
            if allocation.date_to:
                leave_domain.append(('request_date_to', '<=', allocation.date_to))

            used_leaves = request.env['hr.leave'].sudo().search(leave_domain)
            total_used_days = sum(used_leaves.mapped('number_of_days'))
            remaining_days = allocation.number_of_days - total_used_days

            allocation_data.append({
                'leave_type': leave_type.name,
                'total_allocation': allocation.number_of_days,
                'used_days': total_used_days,
                'remaining_days': max(0, remaining_days),
                'allocation_id': allocation.id,
            })

        # Handle Compensatory Days - get ALL current valid allocations
        comp_allocations = request.env['hr.leave.allocation'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('holiday_status_id.name', '=', 'Compensatory Days'),
            ('holiday_status_id.is_portal', '=', True),
            '|',
            ('date_from', '<=', current_date),
            ('date_from', '=', False),
            '|',
            ('date_to', '>=', current_date),
            ('date_to', '=', False)
        ], order='date_from DESC, date_to DESC')
        print("Compensatory allocations", comp_allocations)

        if comp_allocations:
            # Calculate total allocation across all active compensatory allocations
            total_comp_allocation = sum(comp_allocations.mapped('number_of_days'))

            comp_leave_type_id = comp_allocations[0].holiday_status_id.id

            # Find the earliest date_from and latest date_to across all allocations
            date_from_list = [alloc.date_from for alloc in comp_allocations if alloc.date_from]
            date_to_list = [alloc.date_to for alloc in comp_allocations if alloc.date_to]

            earliest_date = min(date_from_list) if date_from_list else False
            latest_date = max(date_to_list) if date_to_list else False

            # Get all leaves within the combined date range (calculated only once)
            leave_domain = [
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', comp_leave_type_id),
                ('state', 'not in', ['refuse', 'cancel'])
            ]

            if earliest_date:
                leave_domain.append(('date_from', '>=', earliest_date))
            if latest_date:
                leave_domain.append(('date_to', '<=', latest_date))

            used_leaves = request.env['hr.leave'].sudo().search(leave_domain)
            total_comp_used = sum(used_leaves.mapped('number_of_days'))

            remaining_comp_days = total_comp_allocation - total_comp_used

            # Show as a single combined allocation entry
            allocation_data.append({
                'leave_type': 'Compensatory Days',
                'total_allocation': total_comp_allocation,
                'used_days': total_comp_used,
                'remaining_days': max(0, remaining_comp_days),
                'allocation_id': comp_allocations[0].id,  # Reference first allocation
                # 'is_combined': len(comp_allocations) > 1,  # Flag for multiple allocations
                # 'allocation_count': len(comp_allocations),
            })

        # Get timeoffs based on user role
        if is_manager:
            timeoffs = request.env['hr.leave'].sudo().search([
                ('employee_id', 'in', subordinates.ids + [employee.id]),
                ('holiday_status_id.is_portal', '=', True)
            ], order='date_from DESC')
        elif is_hr:
            timeoffs = request.env['hr.leave'].sudo().search([
                ('employee_id', 'in', subordinate_emps.ids + [employee.id]),
                ('holiday_status_id.is_portal', '=', True)
            ], order='date_from DESC')
        else:
            timeoffs = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id.is_portal', '=', True)
            ], order='date_from DESC')

        timeoff_data = []
        status_mapping = {
            'draft': 'Draft',
            'confirm': 'To Approve',
            'validate1': 'Second Approval',
            'validate': 'Approved',
            'refuse': 'Refused',
            'cancel': 'Cancelled'
        }

        for timeoff in timeoffs:
            can_approve = (
                    is_manager
                    and timeoff.state in ['confirm']
                    and timeoff.employee_id.id != employee.id
            )
            hr_can_approve = (is_hr and timeoff.state in ['validate1'] and timeoff.employee_id.id != employee.id)
            timeoff_data.append({
                'id': timeoff.id,
                'employee_name': timeoff.employee_id.name,
                'type': timeoff.holiday_status_id.name,
                'start_date': timeoff.date_from.strftime('%Y-%m-%d') if timeoff.date_from else '',
                'end_date': timeoff.date_to.strftime('%Y-%m-%d') if timeoff.date_to else '',
                'duration': timeoff.number_of_days,
                'status': status_mapping.get(timeoff.state, timeoff.state),
                'request_date': timeoff.request_date_to.strftime('%Y-%m-%d') if timeoff.request_date_to else '',
                'can_approve': can_approve,
                'hr_can_approve': hr_can_approve,
            })

        return request.render("visio_tti_timeoff_portal.timeoff_page", {
            'allocations': allocation_data,
            'timeoffs': timeoff_data,
            'employee': employee,
            'is_manager': is_manager,
            'is_hr': is_hr,
        })

    @http.route(['/my/timeoff/approve/<int:leave_id>'], type='http', auth='user', website=True, methods=['POST'])
    def approve_timeoff(self, leave_id, **post):
        try:
            leave = request.env['hr.leave'].sudo().browse(leave_id)
            print("leave", leave)
            print("leave", leave.name)
            print("leave", leave.state)
            if not leave.exists():
                raise UserError("Leave request not found.")

            if leave.state == 'confirm':
                print("leave confirm", leave)
                leave.sudo().action_approve()
            elif leave.state == 'validate1':
                print("leave validate", leave)
                leave.sudo().action_validate()
        except Exception as e:
            _logger.exception("Error approving leave: %s", str(e))
        return request.redirect('/my/timeoffs')

    @http.route(['/my/timeoff/refuse/<int:leave_id>'], type='http', auth='user', website=True, methods=['POST'])
    def refuse_timeoff(self, leave_id, **post):
        try:
            leave = request.env['hr.leave'].sudo().browse(leave_id)
            if not leave.exists():
                raise UserError("Leave request not found.")

            # manager = request.env.user.employee_id
            # if leave.employee_id.parent_id != manager:
            #     raise AccessError("You are not authorized to refuse this leave.")

            if leave.state not in ['refuse', 'cancel']:
                leave.action_refuse()
        except Exception as e:
            _logger.exception("Error refusing leave: %s", str(e))
        return request.redirect('/my/timeoffs')

    @http.route(['/my/timeoff/view/<int:leave_id>'], type='http', auth='user', website=True)
    def view_timeoff_detail(self, leave_id, **kwargs):
        leave = request.env['hr.leave'].sudo().browse(leave_id)
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")

        return request.render("visio_tti_timeoff_portal.timeoff_view_page", {
            'leave': leave,
            'url': base_url,
        })

    @http.route('/my/timeoff/request', type='http', auth="user", website=True)
    def timeoff_request_form(self, **kwargs):
        employee = request.env.user.employee_id
        user = request.env.user
        if not employee:
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            _logger.info("[employee orm ] user=%s", employee and employee.id)

        leave_types = request.env['hr.leave.type'].sudo().search([
            ('requires_allocation', '=', 'no'),
            ('is_portal', '=', True)
        ])

        # Add types with allocation
        current_date = fields.Date.today()
        year_start = f"{current_date.year}-01-01"
        year_end = f"{current_date.year}-12-31"

        allocated_types = request.env['hr.leave.allocation'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('holiday_status_id.requires_allocation', '=', 'yes'),
            ('holiday_status_id.is_portal', '=', True),
            '|',
            ('date_from', '<=', year_end),
            ('date_from', '=', False),
            '|',
            ('date_to', '>=', year_start),
            ('date_to', '=', False),
        ]).mapped('holiday_status_id')

        # Combine all leave types available to the employee
        all_leave_types = leave_types | allocated_types

        return request.render("visio_tti_timeoff_portal.timeoff_request_form", {
            'employee': employee,
            'leave_types': all_leave_types,
            'success': False,
            'error': False
        })

        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/')

        leave_types = request.env['hr.leave.type'].sudo().search([])

        try:
            if not post.get('leave_type_id'):
                raise UserError("Please select a leave type.")

            if not post.get('date_from') or not post.get('date_to'):
                raise UserError("Please provide both start and end dates.")

            # Convert dates from string to datetime
            date_from = datetime.strptime(post.get('date_from'), '%Y-%m-%d')
            date_to = datetime.strptime(post.get('date_to'), '%Y-%m-%d')

            # Set time to business hours
            date_from = date_from.replace(hour=0, minute=0, second=0)
            date_to = date_to.replace(hour=23, minute=59, second=59)

            # Validate date range
            if date_from > date_to:
                raise UserError("End date cannot be before start date.")

            is_half_day = post.get('is_half_day') == 'on'
            # For half day leaves, dates must be the same
            if is_half_day and date_from.date() != date_to.date():
                raise UserError("Half day leave must be for a single day only.")

            # Check for overlapping leave requests
            overlapping_leaves = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', 'not in', ['cancel', 'refuse']),
                '|',
                '&', ('date_from', '<=', date_from), ('date_to', '>=', date_from),
                '&', ('date_from', '<=', date_to), ('date_to', '>=', date_to),
            ])

            if overlapping_leaves:
                # Check if current request is half day
                current_is_half_day = is_half_day
                current_is_single_day = date_from.date() == date_to.date()

                conflicting_leaves = []

                for leave in overlapping_leaves:
                    # Check if existing leave is half day (0.5 days) and single day
                    existing_is_half_day = leave.number_of_days == 0.5
                    existing_is_single_day = leave.date_from.date() == leave.date_to.date() if leave.date_from and leave.date_to else False

                    # If both are half days on the same single day, check if they're exactly the same dates
                    if (current_is_half_day and existing_is_half_day and
                            current_is_single_day and existing_is_single_day and
                            date_from.date() == leave.date_from.date()):

                        # Two half days on the same day are allowed (morning + afternoon)
                        # But if they have the exact same time, it's a conflict
                        if (date_from == leave.date_from and date_to == leave.date_to):
                            conflicting_leaves.append(leave)
                    else:
                        # For all other cases (full day vs any leave, different days, etc.)
                        # Check for actual date overlap
                        leave_start = leave.date_from.date() if leave.date_from else None
                        leave_end = leave.date_to.date() if leave.date_to else None
                        request_start = date_from.date()
                        request_end = date_to.date()

                        if leave_start and leave_end:
                            # Check if there's actual date overlap
                            if not (request_end < leave_start or request_start > leave_end):
                                conflicting_leaves.append(leave)

                if conflicting_leaves:
                    overlapping_dates = []
                    for leave in conflicting_leaves:
                        from_date = leave.date_from.strftime('%m/%d/%Y') if leave.date_from else 'N/A'
                        to_date = leave.date_to.strftime('%m/%d/%Y') if leave.date_to else 'N/A'
                        days_info = f"({leave.number_of_days} days)" if leave.number_of_days != int(
                            leave.number_of_days) else f"({int(leave.number_of_days)} days)"
                        overlapping_dates.append(f"from {from_date} to {to_date} {days_info} - {leave.state.title()}")

                    error_msg = f"You already have time off booked that conflicts with this period:\n" + "\n".join(
                        overlapping_dates)

                    # Add helpful message for half day scenarios
                    if current_is_half_day and any(leave.number_of_days == 0.5 for leave in conflicting_leaves):
                        error_msg += "\n\nNote: You can have multiple half-day leaves on the same day, but not with identical times."

                    raise UserError(error_msg)

            leave_type_id = int(post.get('leave_type_id'))
            leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)

            # Saturday Leaves validation
            if leave_type.name.lower() == 'saturday leaves':
                first_day = date_from.replace(day=1)
                last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)

                saturday_leaves = request.env['hr.leave'].sudo().search_count([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('date_from', '>=', first_day),
                    ('date_from', '<=', last_day),
                ])
                if saturday_leaves >= 1:
                    raise UserError("You can only take one Saturday leave per month.")

                if not is_half_day and date_from.date() != date_to.date():
                    raise UserError("Saturday leave must be a single-day leave on a Saturday.")

                if date_from.weekday() != 5:  # 5 = Saturday
                    raise UserError("Saturday leave can only be taken on a Saturday.")

            # Casual leave monthly limit validation
            if leave_type.name.lower() == 'casual leaves':
                first_day = date_from.replace(day=1)
                last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)

                casual_leaves = request.env['hr.leave'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('date_from', '>=', first_day),
                    ('date_from', '<=', last_day),
                ])
                print("casual leaves", casual_leaves)
                total_casual_days = 0
                for casual in casual_leaves:
                    total_casual_days += casual.number_of_days
                print("total", total_casual_days)

                if total_casual_days >= 3:
                    raise UserError(
                        "You cannot take another casual leave this month. You already have 3 casual leaves.")

            if leave_type.requires_allocation == 'yes':
                if is_half_day:
                    requested_days = 0.5
                else:
                    requested_days = (date_to.date() - date_from.date()).days + 1

                allocation = request.env['hr.leave.allocation'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', '=', 'validate')
                ], limit=1)

                if allocation:
                    used_leaves = request.env['hr.leave'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', 'not in', ['refuse', 'cancel'])
                    ])
                    total_used_days = sum(used_leaves.mapped('number_of_days'))
                    available_days = allocation.number_of_days - total_used_days

                    if requested_days > available_days:
                        raise UserError(
                            f"Insufficient {leave_type.name} balance. You have {available_days} days available but requested {requested_days} days.")
                else:
                    raise UserError(f"No allocation found for {leave_type.name}.")

            attachment_data = []
            uploaded_files = request.httprequest.files.getlist('attachments')

            if uploaded_files:
                for file in uploaded_files:
                    if file and file.filename:
                        # Validate file size (e.g., max 10MB)
                        max_size = 10 * 1024 * 1024  # 10MB in bytes
                        file.seek(0, 2)  # Seek to end to get file size
                        file_size = file.tell()
                        file.seek(0)  # Reset to beginning

                        if file_size > max_size:
                            raise UserError(f"File '{file.filename}' is too large. Maximum size is 10MB.")

                        file_content = file.read()
                        attachment_data.append({
                            'filename': file.filename,
                            'content': base64.b64encode(file_content)
                        })

            leave_values = {
                'holiday_status_id': leave_type_id,
                'employee_id': employee.id,
                'date_from': date_from,
                'date_to': date_to,
                'request_date_from': date_from.date(),
                'request_date_to': date_to.date(),
                'name': post.get('description') or 'Time off request',
                'request_unit_half': True if is_half_day else False,
                'number_of_days': 0.5 if is_half_day else (date_to.date() - date_from.date()).days + 1,
            }

            leave_request = request.env['hr.leave'].sudo().create(leave_values)

            attachment_ids = []
            for attachment_info in attachment_data:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': attachment_info['filename'],
                    'datas': attachment_info['content'],
                    'res_model': 'hr.leave',
                    'res_id': leave_request.id,
                    'type': 'binary',
                    'public': True,
                })
                attachment_ids.append(attachment.id)

            if attachment_ids:
                leave_request.sudo().write({
                    'supported_attachment_ids': [(6, 0, attachment_ids)]
                })

            return request.render("visio_tti_timeoff_portal.timeoff_request_form", {
                'employee': employee,
                'leave_types': leave_types,
                'success': True,
                'error': False
            })

        except (UserError, ValidationError) as e:
            return request.render("visio_tti_timeoff_portal.timeoff_request_form", {
                'employee': employee,
                'leave_types': leave_types,
                'success': False,
                'error': str(e),
                'form_data': {
                    'leave_type_id': post.get('leave_type_id'),
                    'date_from': post.get('date_from'),
                    'date_to': post.get('date_to'),
                    'description': post.get('description'),
                    'is_half_day': post.get('is_half_day'),
                }
            })

        except Exception as e:
            _logger.error("Unexpected error in timeoff submission: %s", str(e), exc_info=True)
            return request.render("visio_tti_timeoff_portal.timeoff_request_form", {
                'employee': employee,
                'leave_types': leave_types,
                'success': False,
                'error': "An unexpected error occurred. Please try again or contact support.",
                'form_data': {
                    'leave_type_id': post.get('leave_type_id'),
                    'date_from': post.get('date_from'),
                    'date_to': post.get('date_to'),
                    'description': post.get('description'),
                }
            })

    @http.route('/my/timeoff/submit', type='http', auth="user", website=True, methods=['POST'])
    def timeoff_submit(self, **post):
        # employee = request.env.user.employee_id
        # if not employee:
        #     return request.redirect('/')

        # -------------------------

        employee = request.env.user.employee_id
        user = request.env.user
        if not employee:
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            _logger.info("[employee orm submit] user=%s", employee and employee.id)

        if not employee:
            return request.redirect('/')

        # -------------------------

        leave_types = request.env['hr.leave.type'].sudo().search([])
        try:
            if not post.get('leave_type_id'):
                raise UserError("Please select a leave type.")

            if not post.get('date_from') or not post.get('date_to'):
                raise UserError("Please provide both start and end dates.")

            # Convert dates from string to datetime
            date_from = datetime.strptime(post.get('date_from'), '%Y-%m-%d')
            date_to = datetime.strptime(post.get('date_to'), '%Y-%m-%d')

            # Set time to business hours
            date_from = date_from.replace(hour=0, minute=0, second=0)
            date_to = date_to.replace(hour=23, minute=59, second=59)

            # Validate date range
            if date_from > date_to:
                raise UserError("End date cannot be before start date.")

            is_half_day = post.get('is_half_day') == 'on'
            # For half day leaves, dates must be the same
            if is_half_day and date_from.date() != date_to.date():
                raise UserError("Half day leave must be for a single day only.")

            # If half-day, we require and apply the AM/PM period to compute times
            if is_half_day:
                period = (post.get('request_date_from_period') or '').strip()
                if period not in ('am', 'pm'):
                    raise UserError("Please select the half-day period (AM or PM).")

                if period == 'am':
                    date_from = datetime.combine(date_from.date(), time(9, 0))
                    date_to = datetime.combine(date_from.date(), time(13, 0))
                else:  # 'pm'
                    date_from = datetime.combine(date_from.date(), time(14, 0))
                    date_to = datetime.combine(date_from.date(), time(18, 0))

            # Check for overlapping leave requests
            overlapping_leaves = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', 'not in', ['cancel', 'refuse']),
                '|',
                '&', ('date_from', '<=', date_from), ('date_to', '>=', date_from),
                '&', ('date_from', '<=', date_to), ('date_to', '>=', date_to),
            ])

            if overlapping_leaves:
                # Check if current request is half day
                current_is_half_day = is_half_day
                current_is_single_day = date_from.date() == date_to.date()

                conflicting_leaves = []

                for leave in overlapping_leaves:
                    # Check if existing leave is half day (0.5 days) and single day
                    existing_is_half_day = leave.number_of_days == 0.5
                    existing_is_single_day = leave.date_from.date() == leave.date_to.date() if leave.date_from and leave.date_to else False

                    # If both are half days on the same single day, check if they're exactly the same dates
                    if (current_is_half_day and existing_is_half_day and
                            current_is_single_day and existing_is_single_day and
                            date_from.date() == leave.date_from.date()):

                        # Two half days on the same day are allowed (morning + afternoon)
                        # But if they have the exact same time, it's a conflict
                        if (date_from == leave.date_from and date_to == leave.date_to):
                            conflicting_leaves.append(leave)
                    else:
                        # For all other cases (full day vs any leave, different days, etc.)
                        # Check for actual date overlap
                        leave_start = leave.date_from.date() if leave.date_from else None
                        leave_end = leave.date_to.date() if leave.date_to else None
                        request_start = date_from.date()
                        request_end = date_to.date()

                        if leave_start and leave_end:
                            # Check if there's actual date overlap
                            if not (request_end < leave_start or request_start > leave_end):
                                conflicting_leaves.append(leave)

                if conflicting_leaves:
                    overlapping_dates = []
                    for leave in conflicting_leaves:
                        from_date = leave.date_from.strftime('%m/%d/%Y') if leave.date_from else 'N/A'
                        to_date = leave.date_to.strftime('%m/%d/%Y') if leave.date_to else 'N/A'
                        days_info = f"({leave.number_of_days} days)" if leave.number_of_days != int(
                            leave.number_of_days) else f"({int(leave.number_of_days)} days)"
                        overlapping_dates.append(f"from {from_date} to {to_date} {days_info} - {leave.state.title()}")

                    error_msg = f"You already have time off booked that conflicts with this period:\n" + "\n".join(
                        overlapping_dates)

                    # Add helpful message for half day scenarios
                    if current_is_half_day and any(leave.number_of_days == 0.5 for leave in conflicting_leaves):
                        error_msg += "\n\nNote: You can have multiple half-day leaves on the same day, but not with identical times."

                    raise UserError(error_msg)

            leave_type_id = int(post.get('leave_type_id'))
            leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)

            # Saturday Leaves validation
            if leave_type.name.lower() == 'saturday leaves':
                first_day = date_from.replace(day=1)
                last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)

                saturday_leaves = request.env['hr.leave'].sudo().search_count([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('date_from', '>=', first_day),
                    ('date_from', '<=', last_day),
                ])
                if saturday_leaves >= 1:
                    raise UserError("You can only take one Saturday leave per month.")

                if not is_half_day and date_from.date() != date_to.date():
                    raise UserError("Saturday leave must be a single-day leave on a Saturday.")

                if date_from.weekday() != 5:  # 5 = Saturday
                    raise UserError("Saturday leave can only be taken on a Saturday.")

            # Casual leave monthly limit validation
            if leave_type.name.lower() == 'casual leaves':
                first_day = date_from.replace(day=1)
                last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)

                casual_leaves = request.env['hr.leave'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('date_from', '>=', first_day),
                    ('date_from', '<=', last_day),
                ])
                print("casual leaves", casual_leaves)
                total_casual_days = 0
                for casual in casual_leaves:
                    total_casual_days += casual.number_of_days
                print("total", total_casual_days)

                if total_casual_days >= 3:
                    raise UserError(
                        "You cannot take another casual leave this month. You already have 3 casual leaves.")

            if leave_type.requires_allocation == 'yes':
                if is_half_day:
                    requested_days = 0.5
                else:
                    requested_days = 0
                    current_date = date_from.date()
                    end_date = date_to.date()

                    while current_date <= end_date:
                        if current_date.weekday() != 6:
                            requested_days += 1
                        current_date += timedelta(days=1)

                # Handle Compensatory Days separately
                if leave_type.name == 'Compensatory Days':
                    current_date = fields.Date.today()

                    # Get all active compensatory allocations
                    comp_allocations = request.env['hr.leave.allocation'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('state', '=', 'validate'),
                        ('holiday_status_id', '=', leave_type.id),
                        ('holiday_status_id.is_portal', '=', True),
                        '|',
                        ('date_from', '<=', current_date),
                        ('date_from', '=', False),
                        '|',
                        ('date_to', '>=', current_date),
                        ('date_to', '=', False)
                    ])

                    if not comp_allocations:
                        raise UserError(f"No allocation found for {leave_type.name}.")

                    # Calculate total allocation across all active compensatory allocations
                    total_comp_allocation = sum(comp_allocations.mapped('number_of_days'))

                    # Find the earliest date_from and latest date_to across all allocations
                    date_from_list = [alloc.date_from for alloc in comp_allocations if alloc.date_from]
                    date_to_list = [alloc.date_to for alloc in comp_allocations if alloc.date_to]

                    earliest_date = min(date_from_list) if date_from_list else False
                    latest_date = max(date_to_list) if date_to_list else False

                    # Get all used leaves within the combined date range
                    leave_domain = [
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', 'not in', ['refuse', 'cancel'])
                    ]

                    if earliest_date:
                        leave_domain.append(('date_from', '>=', earliest_date))
                    if latest_date:
                        leave_domain.append(('date_to', '<=', latest_date))

                    used_leaves = request.env['hr.leave'].sudo().search(leave_domain)
                    total_used_days = sum(used_leaves.mapped('number_of_days'))
                    available_days = total_comp_allocation - total_used_days

                    if requested_days > available_days:
                        raise UserError(
                            f"Insufficient {leave_type.name} balance. You have {available_days} days available but requested {requested_days} days.")

                else:
                    current_date = fields.Date.today()
                    year_start = date(current_date.year, 1, 1)
                    year_end = date(current_date.year, 12, 31)
                    allocations = request.env['hr.leave.allocation'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', '=', 'validate'),
                        '|', ('date_from', '<=', year_end), ('date_from', '=', False),
                        '|', ('date_to', '>=', year_start), ('date_to', '=', False),
                    ])

                    if not allocations:
                        raise UserError(f"No allocation found for {leave_type.name}.")

                    total_remaining = 0.0

                    for allocation in allocations:
                        alloc_start = allocation.date_from or year_start
                        alloc_end = allocation.date_to or year_end
                        # clamp to current year
                        alloc_start = max(alloc_start, year_start)
                        alloc_end = min(alloc_end, year_end)

                        used_leaves = request.env['hr.leave'].sudo().search([
                            ('employee_id', '=', employee.id),
                            ('holiday_status_id', '=', leave_type.id),
                            ('state', 'not in', ['refuse', 'cancel']),
                            ('date_from', '>=', alloc_start),
                            ('date_to', '<=', alloc_end),
                        ])

                        used_days = sum(used_leaves.mapped('number_of_days'))
                        remaining = allocation.number_of_days - used_days
                        total_remaining += max(0, remaining)

                    if requested_days > total_remaining:
                        raise UserError(
                            f"Insufficient {leave_type.name} balance. "
                            f"You have {total_remaining} days available but requested {requested_days} days."
                        )

            attachment_data = []
            uploaded_files = request.httprequest.files.getlist('attachments')

            if uploaded_files:
                for file in uploaded_files:
                    if file and file.filename:
                        # Validate file size (e.g., max 10MB)
                        max_size = 10 * 1024 * 1024  # 10MB in bytes
                        file.seek(0, 2)  # Seek to end to get file size
                        file_size = file.tell()
                        file.seek(0)  # Reset to beginning

                        if file_size > max_size:
                            raise UserError(f"File '{file.filename}' is too large. Maximum size is 10MB.")

                        file_content = file.read()
                        attachment_data.append({
                            'filename': file.filename,
                            'content': base64.b64encode(file_content)
                        })

            leave_values = {
                'holiday_status_id': leave_type_id,
                'employee_id': employee.id,
                'date_from': date_from,
                'date_to': date_to,
                'request_date_from': date_from.date(),
                'request_date_to': date_to.date(),
                'name': post.get('description') or 'Time off request',
                'request_unit_half': True if is_half_day else False,
                'request_date_from_period': post.get('request_date_from_period') if is_half_day else False,  # ← NEW
                'number_of_days': 0.5 if is_half_day else (date_to.date() - date_from.date()).days + 1,
            }

            leave_request = request.env['hr.leave'].sudo().create(leave_values)

            attachment_ids = []
            for attachment_info in attachment_data:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': attachment_info['filename'],
                    'datas': attachment_info['content'],
                    'res_model': 'hr.leave',
                    'res_id': leave_request.id,
                    'type': 'binary',
                    'public': True,
                })
                attachment_ids.append(attachment.id)

            if attachment_ids:
                leave_request.sudo().write({
                    'supported_attachment_ids': [(6, 0, attachment_ids)]
                })

            # return request.render("visio_tti_timeoff_portal.timeoff_request_form", {
            #     'employee': employee,
            #     'leave_types': leave_types,
            #     'success': True,
            #     'error': False
            # })

            return request.redirect('/my/timeoffs')


        except (UserError, ValidationError) as e:
            return request.render("visio_tti_timeoff_portal.timeoff_request_form", {
                'employee': employee,
                'leave_types': leave_types,
                'success': False,
                'error': str(e),
                'form_data': {
                    'leave_type_id': post.get('leave_type_id'),
                    'date_from': post.get('date_from'),
                    'date_to': post.get('date_to'),
                    'description': post.get('description'),
                    'is_half_day': post.get('is_half_day'),
                    'request_date_from_period': post.get('request_date_from_period'),  # ← add this
                }

            })

        except Exception as e:
            _logger.error("Unexpected error in timeoff submission: %s", str(e), exc_info=True)
            return request.render("visio_tti_timeoff_portal.timeoff_request_form", {
                'employee': employee,
                'leave_types': leave_types,
                'success': False,
                'error': "An unexpected error occurred. Please try again or contact support.",
                'form_data': {
                    'leave_type_id': post.get('leave_type_id'),
                    'date_from': post.get('date_from'),
                    'date_to': post.get('date_to'),
                    'description': post.get('description'),
                    'is_half_day': post.get('is_half_day'),
                    'request_date_from_period': post.get('request_date_from_period'),
                }

            })
