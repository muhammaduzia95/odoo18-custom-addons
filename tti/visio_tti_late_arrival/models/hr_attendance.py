import logging
from odoo import fields, models, api
import pytz

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    late_arrival = fields.Float(string="Late Arrival", compute="_compute_late_arrival", store=True)
    late = fields.Boolean(string="Is Late", default=False)
    auto_checkout = fields.Boolean(string="Auto Entry", default=False)

    @api.depends('check_in', 'employee_id', 'employee_id.resource_calendar_id')
    def _compute_late_arrival(self):
        tz = pytz.timezone('Asia/Karachi')

        for attendance in self:
            attendance.late_arrival = 0.0
            try:
                employee = attendance.employee_id
                check_in = attendance.check_in

                if not employee or not check_in or not employee.resource_calendar_id:
                    continue

                check_in_local = pytz.utc.localize(check_in).astimezone(tz)

                day_of_week = str(check_in_local.weekday())
                cal = employee.resource_calendar_id

                calendar_line = cal.attendance_ids.filtered(
                    lambda l: l.dayofweek == day_of_week and l.day_period == 'morning'
                )

                if not calendar_line:
                    continue

                start_hour = float(calendar_line[0].hour_from)
                hour_int = int(start_hour)
                minute_int = int((start_hour - hour_int) * 60)
                expected_start_local = check_in_local.replace(hour=hour_int, minute=minute_int, second=0, microsecond=0)

                check_in_minutes_only = check_in_local.replace(second=0, microsecond=0)

                diff_minutes = (check_in_minutes_only - expected_start_local).total_seconds() / 60.0

                grace_period = 20  # minutes
                if diff_minutes <= grace_period:
                    attendance.late_arrival = 0.0
                    attendance.late = False
                elif diff_minutes > grace_period:
                    late_minutes = diff_minutes
                    attendance.late_arrival = late_minutes / 60.0
                    attendance.late = True
                else:
                    attendance.late_arrival = 0.0

            except Exception as e:
                print(f"❌ Error computing late arrival for attendance {attendance.id}: {e}")
