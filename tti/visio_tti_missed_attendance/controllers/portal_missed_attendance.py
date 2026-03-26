# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_missed_attendance\controllers\portal_missed_attendance.py
from odoo import http
from odoo.http import request
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)


class PortalMissedAttendance(http.Controller):

    # Helper: get employee linked to current user
    def _get_employee(self):
        employee = request.env.user.employee_id
        _logger.info("[_get_employee] Using request.env.user.employee_id -> %s", employee and employee.id)
        return employee

    # Helper: compute This Month Attendance + Missing Days
    def _get_month_data(self, employee):
        _logger.info("[_get_month_data] Start, employee=%s", employee and f"{employee.id} - {employee.name}")
        month_lines = []
        missing_days = []

        if not employee:
            _logger.warning("[_get_month_data] No employee provided, returning empty lists")
            return month_lines, missing_days

        today = date.today()
        first_day = today.replace(day=1)
        _logger.info("[_get_month_data] today=%s, first_day_of_month=%s", today, first_day)

        Attendance = request.env['hr.attendance'].sudo()
        Leave = request.env['hr.leave'].sudo()

        # Attendance for this month
        from datetime import time as dt_time  # add in imports

        start_dt = datetime.combine(first_day, dt_time.min)
        end_dt = datetime.combine(today + timedelta(days=1), dt_time.min)

        attendance_domain = [
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_dt),
            ('check_in', '<', end_dt),
        ]

        _logger.debug("[_get_month_data] Attendance search domain=%s", attendance_domain)
        attendances = Attendance.search(attendance_domain)
        _logger.info("[_get_month_data] Found %s attendance records", len(attendances))

        # Map date -> {check_in, check_out}
        attendance_by_date = {}
        for att in attendances:
            if not att.check_in:
                _logger.debug("[_get_month_data] Skipping attendance id=%s with no check_in", att.id)
                continue
            d = att.check_in.date()
            data = attendance_by_date.setdefault(d, {'check_in': False, 'check_out': False})
            # earliest check_in
            if not data['check_in'] or att.check_in < data['check_in']:
                _logger.debug(
                    "[_get_month_data] Updating earliest check_in for %s: %s -> %s",
                    d, data['check_in'], att.check_in
                )
                data['check_in'] = att.check_in
            # latest check_out
            if att.check_out:
                if not data['check_out'] or att.check_out > data['check_out']:
                    _logger.debug(
                        "[_get_month_data] Updating latest check_out for %s: %s -> %s",
                        d, data['check_out'], att.check_out
                    )
                    data['check_out'] = att.check_out
        _logger.debug("[_get_month_data] attendance_by_date keys=%s", list(attendance_by_date.keys()))

        # Approved leaves (validated)
        leave_domain = [
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', today),
            ('request_date_to', '>=', first_day),
        ]
        _logger.debug("[_get_month_data] Leave search domain=%s", leave_domain)
        leaves = Leave.search(leave_domain)
        _logger.info("[_get_month_data] Found %s leave records", len(leaves))

        # Map date -> list of leaves
        leave_by_date = {}
        for lv in leaves:
            d = lv.request_date_from
            _logger.debug(
                "[_get_month_data] Processing leave id=%s from %s to %s",
                lv.id, lv.request_date_from, lv.request_date_to
            )
            while d <= lv.request_date_to:
                if first_day <= d <= today:
                    leave_by_date.setdefault(d, []).append(lv)
                    _logger.debug("[_get_month_data] Adding leave id=%s to date %s", lv.id, d)
                d += timedelta(days=1)
        _logger.debug("[_get_month_data] leave_by_date keys=%s", list(leave_by_date.keys()))

        current = first_day
        while current <= today:
            att_data = attendance_by_date.get(current)
            leave_list = leave_by_date.get(current, [])

            _logger.debug(
                "[_get_month_data][%s] att_data=%s, leave_list_len=%s, weekday=%s",
                current, bool(att_data), len(leave_list), current.weekday()
            )

            # Build leave text
            leave_texts = []
            for l in leave_list:
                leave_type = l.holiday_status_id.name or "Leave"
                leave_name = (l.name or "").strip()
                if leave_name:
                    leave_texts.append(f"{leave_type} - {leave_name}")
                else:
                    leave_texts.append(leave_type)
            leave_text = ", ".join(leave_texts)

            # For Sundays with no leave, show "Sunday" in leave column
            leave_text_for_line = leave_text
            if not leave_text_for_line and current.weekday() == 6:
                leave_text_for_line = "Sunday"

            # Full attendance = both check_in and check_out present
            has_full_attendance = bool(
                att_data and att_data.get('check_in') and att_data.get('check_out')
            )
            _logger.debug(
                "[_get_month_data][%s] has_full_attendance=%s, leave_text_for_line=%s",
                current, has_full_attendance, leave_text_for_line
            )

            # ---------- TABLE 2: This Month Attendance ----------
            # show:
            #  - full attendance
            #  - any leave
            #  - Sundays (even with no attendance/leave)
            if has_full_attendance or leave_list or current.weekday() == 6:
                month_lines.append({
                    'date': current,
                    'check_in': att_data['check_in'] if att_data else False,
                    'check_out': att_data['check_out'] if att_data else False,
                    'leave_text': leave_text_for_line,
                })
                _logger.debug(
                    "[_get_month_data][%s] Added to month_lines: check_in=%s, check_out=%s, leave_text=%s",
                    current,
                    att_data['check_in'] if att_data else False,
                    att_data['check_out'] if att_data else False,
                    leave_text_for_line,
                )

            # ---------- TABLE 3: Missing Days ----------
            # conditions (excluding Sundays):
            #  - no attendance AND no leave
            #  - OR partial attendance (only check_in OR only check_out) AND no leave
            missing_condition = False
            if current.weekday() != 6:  # skip Sundays entirely here
                if not att_data and not leave_list:
                    missing_condition = True
                elif att_data and not leave_list and (not att_data.get('check_in') or not att_data.get('check_out')):
                    missing_condition = True

            _logger.debug(
                "[_get_month_data][%s] missing_condition=%s",
                current, missing_condition
            )

            if missing_condition:
                missing_days.append({
                    'date': current,
                    'check_in': att_data.get('check_in') if att_data else False,
                    'check_out': att_data.get('check_out') if att_data else False,
                })
                _logger.debug(
                    "[_get_month_data][%s] Added to missing_days: check_in=%s, check_out=%s",
                    current,
                    att_data.get('check_in') if att_data else False,
                    att_data.get('check_out') if att_data else False,
                )

            current += timedelta(days=1)

        _logger.info(
            "[_get_month_data] Completed. month_lines=%s, missing_days=%s",
            len(month_lines), len(missing_days)
        )
        return month_lines, missing_days

    # LIST PAGE
    @http.route(['/my/missed-attendance'], type='http', auth='user', website=True)
    def portal_missed_attendance_list(self, **kw):
        _logger.info("[portal_missed_attendance_list] Called with kw=%s", kw)
        employee = self._get_employee()
        month_lines, missing_days = self._get_month_data(employee) if employee else ([], [])
        _logger.info(
            "[portal_missed_attendance_list] employee_id=%s, month_lines=%s, missing_days=%s",
            employee and employee.id, len(month_lines), len(missing_days)
        )

        # Existing missed attendance requests
        Requests = request.env['missed.attendance.request'].sudo()
        req_domain = [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)]
        _logger.debug("[portal_missed_attendance_list] Request search domain=%s", req_domain)
        missed_requests = Requests.search(req_domain, order="date desc")
        _logger.info(
            "[portal_missed_attendance_list] Found %s missed.attendance.request records",
            len(missed_requests)
        )

        values = {
            'employee': employee,
            'missed_list': missed_requests,   # table 1
            'month_lines': month_lines,       # table 2
            'missing_days': missing_days,     # table 3 + create form
        }
        _logger.debug("[portal_missed_attendance_list] Rendering template with values keys=%s", list(values.keys()))
        return request.render('visio_tti_missed_attendance.missed_attendance_list', values)

    # CREATE FORM PAGE
    @http.route('/my/missed-attendance/new', type='http', auth='user', website=True)
    def portal_missed_attendance_create(self, **kw):
        _logger.info("[portal_missed_attendance_create] Called with kw=%s", kw)
        employee = self._get_employee()
        _, missing_days = self._get_month_data(employee) if employee else ([], [])
        _logger.info(
            "[portal_missed_attendance_create] employee_id=%s, missing_days=%s",
            employee and employee.id, len(missing_days)
        )
        values = {
            'employee': employee,
            'missing_days': missing_days,
        }
        _logger.debug("[portal_missed_attendance_create] Rendering template with values keys=%s", list(values.keys()))
        return request.render('visio_tti_missed_attendance.missed_attendance_create', values)

    # SUBMIT FORM
    @http.route('/my/missed-attendance/submit', type='http', auth='user', methods=['POST'], website=True)
    def portal_missed_attendance_submit(self, **post):
        _logger.info("[portal_missed_attendance_submit] Called with post=%s", post)
        employee = self._get_employee()
        if not employee:
            _logger.error("[portal_missed_attendance_submit] No employee linked to portal user")
            return request.render('visio_tti_missed_attendance.portal_error', {
                'error_message': 'No employee is linked to your portal user.'
            })

        selected_date_str = post.get('date')
        _logger.info("[portal_missed_attendance_submit] selected_date_str=%s", selected_date_str)
        if not selected_date_str:
            _logger.warning("[portal_missed_attendance_submit] No date selected")
            return request.render('visio_tti_missed_attendance.portal_error', {
                'error_message': 'Please select a date.'
            })

        try:
            selected_date = date.fromisoformat(selected_date_str)
            _logger.info("[portal_missed_attendance_submit] Parsed selected_date=%s", selected_date)
        except ValueError:
            _logger.exception("[portal_missed_attendance_submit] Invalid date format: %s", selected_date_str)
            return request.render('visio_tti_missed_attendance.portal_error', {
                'error_message': 'Invalid date format.'
            })

        # Recompute missing days and ensure selected date is truly missing
        _, missing_days = self._get_month_data(employee)
        _logger.debug(
            "[portal_missed_attendance_submit] Recomputed missing_days=%s",
            len(missing_days)
        )
        allowed_dates = {line['date'] for line in missing_days}
        _logger.debug(
            "[portal_missed_attendance_submit] allowed_dates=%s",
            allowed_dates
        )

        if selected_date not in allowed_dates:
            _logger.warning(
                "[portal_missed_attendance_submit] selected_date=%s not in allowed_dates",
                selected_date
            )
            return request.render('visio_tti_missed_attendance.portal_error', {
                'error_message': 'You can only request for days with missing attendance and no leave.'
            })

        check_in_time = (post.get('check_in_time') or '').strip()
        check_out_time = (post.get('check_out_time') or '').strip()
        _logger.info(
            "[portal_missed_attendance_submit] Form times - check_in_time=%s, check_out_time=%s",
            check_in_time, check_out_time
        )

        if not check_in_time or not check_out_time:
            _logger.warning(
                "[portal_missed_attendance_submit] Missing check_in_time or check_out_time"
            )
            return request.render('visio_tti_missed_attendance.portal_error', {
                'error_message': 'Check In and Check Out time are required.'
            })

        try:
            check_in_dt = datetime.fromisoformat(f"{selected_date_str}T{check_in_time}")
            check_out_dt = datetime.fromisoformat(f"{selected_date_str}T{check_out_time}")
            _logger.info(
                "[portal_missed_attendance_submit] Parsed check_in_dt=%s, check_out_dt=%s",
                check_in_dt, check_out_dt
            )
        except ValueError:
            _logger.exception("[portal_missed_attendance_submit] Invalid time format")
            return request.render('visio_tti_missed_attendance.portal_error', {
                'error_message': 'Invalid time format.'
            })

        # Create missed attendance request (state = draft)
        _logger.info(
            "[portal_missed_attendance_submit] Creating missed.attendance.request with "
            "employee_id=%s, check_in=%s, check_out=%s, reason=%s",
            employee.id, check_in_dt, check_out_dt, post.get('reason')
        )
        request.env['missed.attendance.request'].sudo().create({
            'employee_id': employee.id,
            'check_in': check_in_dt,
            'check_out': check_out_dt,
            'reason': post.get('reason'),
        })

        _logger.info("[portal_missed_attendance_submit] Redirecting to /my/missed-attendance")
        return request.redirect('/my/missed-attendance')
