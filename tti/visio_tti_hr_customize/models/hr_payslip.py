from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, time

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        for payslip in self:
            employee = payslip.employee_id
            date_from = payslip.date_from
            date_to = payslip.date_to

            missing_days = []

            current_day = date_from
            while current_day <= date_to:
                if current_day.weekday() != 6:
                    # Check attendance
                    has_attendance = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', employee.id),
                        ('check_in', '>=', datetime.combine(current_day, time.min)),
                        ('check_in', '<=', datetime.combine(current_day, time.max))
                    ]) > 0

                    # Check time off
                    has_leave = self.env['hr.leave'].search_count([
                        ('employee_id', '=', employee.id),
                        ('state', '=', 'validate'),
                        ('request_date_from', '<=', current_day),
                        ('request_date_to', '>=', current_day)
                    ]) > 0

                    if not has_attendance and not has_leave:
                        missing_days.append(current_day.strftime('%Y-%m-%d'))

                current_day += timedelta(days=1)

            # if missing_days:
            #     raise ValidationError(
            #         f"There are {len(missing_days)} working days have no attendance or approved time off for employee {employee.name}:\n\n"
            #         + " - ".join(missing_days)
            #     )

        return super().compute_sheet()
