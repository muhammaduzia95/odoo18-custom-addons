from odoo import models, fields
import pytz
from pytz import timezone, UTC
from dateutil.relativedelta import relativedelta
from odoo.tools.translate import _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, time

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_portal = fields.Boolean(string="Visible to Portal Users", default=False)

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def action_validate(self, check_state=True):
        current_employee = self.env.user.employee_id.sudo()

        leaves = self._get_leaves_on_public_holiday()
        if leaves:
            raise ValidationError(
                _('The following employees are not supposed to work during that period:\n %s') % ','.join(
                    leaves.mapped('employee_id.name')))

        if check_state and any(
                holiday.state not in ['confirm', 'validate1'] and holiday.validation_type != 'no_validation' for holiday
                in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.sudo().write({'state': 'validate'})

        leaves_second_approver = self.env['hr.leave']
        leaves_first_approver = self.env['hr.leave']

        for leave in self:
            if leave.validation_type == 'both':
                leaves_second_approver += leave
            else:
                leaves_first_approver += leave

        leaves_second_approver.sudo().write({'second_approver_id': current_employee.id})
        leaves_first_approver.sudo().write({'first_approver_id': current_employee.id})

        self._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            self.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()

        return True

    def _validate_leave_request(self):
        """ Validate time off requests
        by creating a calendar event and a resource time off. """
        holidays = self.filtered("employee_id")
        holidays.sudo()._create_resource_leave()  # Apply sudo here as well

        meeting_holidays = holidays.filtered(lambda l: l.holiday_status_id.create_calendar_meeting)
        meetings = self.env['calendar.event']
        if meeting_holidays:
            meeting_values_for_user_id = meeting_holidays._prepare_holidays_meeting_values()
            Meeting = self.env['calendar.event']
            for user_id, meeting_values in meeting_values_for_user_id.items():
                meetings += Meeting.with_user(user_id or self.env.uid).sudo().with_context(
                    allowed_company_ids=[],
                    no_mail_to_attendees=True,
                    calendar_no_videocall=True,
                    active_model=self._name
                ).create(meeting_values)

        Holiday = self.env['hr.leave']
        for meeting in meetings:
            Holiday.browse(meeting.res_id).sudo().meeting_id = meeting

        for holiday in holidays:
            user_tz = timezone(holiday.tz)
            utc_tz = pytz.utc.localize(holiday.date_from).astimezone(user_tz)
            notify_partner_ids = holiday.employee_id.user_id.partner_id.ids
            holiday.sudo().message_post(
                body=_(
                    'Your %(leave_type)s planned on %(date)s has been accepted',
                    leave_type=holiday.holiday_status_id.display_name,
                    date=utc_tz.replace(tzinfo=None)
                ),
                partner_ids=notify_partner_ids
            )

    def _check_double_validation_rules(self, employees, state):
        if self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
            return

        is_leave_user = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        # if state == 'validate1':
        #     employees = employees.filtered(lambda employee: employee.parent_id != self.env.user)
        #     if employees and not is_leave_user:
        #         raise AccessError(_('You cannot first approve a time off for %s, because you are not his time off manager', employees[0].name))
        # elif state == 'validate' and not is_leave_user:
        #     # Is probably handled via ir.rule
        #     raise AccessError(_('You don\'t have the rights to apply second approval on a time off request'))