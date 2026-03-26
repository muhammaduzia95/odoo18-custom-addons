from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, time
import pytz
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    MAX_CHECK_DAYS = 10

    @api.model_create_multi
    def create(self, vals):
        attendance = super().create(vals)
        employee = attendance.employee_id
        check_in = attendance.check_in.replace(tzinfo=None)  # naive UTC

        if self._is_late(attendance, employee, check_in):
            if self._is_late_three_previous_days(employee, check_in):
                self._deduct_annual_leave(employee, check_in)

        return attendance

    def _get_shift_start(self, employee, dt):
        """
        Returns the weekly fixed shift start and end time based on the resource calendar.
        Assumes same shift time for every weekday.
        """
        calendar = employee.resource_calendar_id
        if not calendar or not calendar.attendance_ids:
            return None, None

        user_tz = pytz.timezone(employee.tz or self.env.user.tz or 'UTC')
        local_dt = pytz.UTC.localize(dt).astimezone(user_tz)
        local_date = local_dt.date()

        # Sort all attendance lines by hour
        sorted_attendance = calendar.attendance_ids.sorted(lambda a: a.hour_from)

        # First shift start time
        hour_from = sorted_attendance[0].hour_from
        shift_start_local = datetime.combine(local_date, time(
            hour=int(hour_from),
            minute=int((hour_from % 1) * 60)
        ))

        # Last shift end time
        hour_to = max(line.hour_to for line in sorted_attendance)
        shift_end_local = datetime.combine(local_date, time(
            hour=int(hour_to),
            minute=int((hour_to % 1) * 60)
        ))

        # Convert both to UTC and strip tzinfo
        shift_start_utc = user_tz.localize(shift_start_local).astimezone(pytz.UTC).replace(tzinfo=None)
        shift_end_utc = user_tz.localize(shift_end_local).astimezone(pytz.UTC).replace(tzinfo=None)

        return shift_start_utc, shift_end_utc

    def _is_late(self, attendance, employee, check_in):
        shift_start, _ = self._get_shift_start(employee, check_in)
        if not shift_start:
            return False
        return check_in > shift_start

    def _is_late_three_previous_days(self, employee, current_dt):
        late_days = 0
        checked_days = 0
        date = current_dt.date() - timedelta(days=1)

        while checked_days < 3 and (current_dt.date() - date).days <= self.MAX_CHECK_DAYS:
            start = datetime.combine(date, time.min)
            end = datetime.combine(date, time.max)

            att = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start),
                ('check_in', '<=', end)
            ], limit=1)

            if att:
                checked_days += 1
                if self._is_late(att, employee, att.check_in.replace(tzinfo=None)):
                    late_days += 1
                else:
                    return False
            date -= timedelta(days=1)

        return late_days == 3

    def _deduct_annual_leave(self, employee, date):
        leave_type = self.env['hr.leave.type'].search([('name', '=', 'Annual Leaves')], limit=1)
        if not leave_type:
            return

        allocation = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id', '=', leave_type.id),
            ('state', '=', 'validate'),
            ('number_of_days', '>', 0)
        ], limit=1)

        if not allocation or allocation.number_of_days <= 0:
            return
        allocation.number_of_days -= 1