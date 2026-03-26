# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_atten_leave_policy\models\late_clockin.py
from odoo import api, fields, models
from datetime import timedelta


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    is_late = fields.Boolean(string="Is Late", default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to tag late arrivals and handle leave deduction."""
        records = super(HrAttendance, self).create(vals_list)
        for rec in records:
            rec._compute_is_late()
            if rec.is_late:
                print(f"[LATE DETECTED] {rec.employee_id.name} checked in at {rec.check_in}")
                rec._apply_late_deduction()
        return records

    def write(self, vals):
        """Re-evaluate lateness if check_in changes."""
        res = super(HrAttendance, self).write(vals)
        if 'check_in' in vals:
            for rec in self:
                rec._compute_is_late()
                if rec.is_late:
                    print(f"[LATE UPDATED] {rec.employee_id.name} re-evaluated as late on {rec.check_in}")
                    rec._apply_late_deduction()
        return res

    def _compute_is_late(self):
        """Tag attendance as Late if check-in > scheduled start + 20 mins."""
        for rec in self:
            if not rec.check_in or not rec.employee_id:
                continue

            # Get work schedule from contract
            contract = rec.employee_id.contract_id
            calendar = contract.resource_calendar_id if contract else False
            if not calendar:
                print(f"[INFO] {rec.employee_id.name} has no work schedule, skipping late check.")
                continue

            # Default start time = 9:00 AM
            default_start = rec.check_in.replace(hour=9, minute=0, second=0, microsecond=0)

            # Fetch earliest start hour for that weekday from calendar
            attendances = calendar.attendance_ids.filtered(
                lambda a: a.dayofweek == str(rec.check_in.weekday())
            )
            if attendances:
                start_hour = min(attendances.mapped('hour_from'))
                start_dt = rec.check_in.replace(hour=int(start_hour),
                                                minute=int((start_hour % 1) * 60),
                                                second=0, microsecond=0)
            else:
                start_dt = default_start

            grace_time = start_dt + timedelta(minutes=20)

            if rec.check_in > grace_time:
                rec.is_late = True
                rec.late_arrival = (rec.check_in - start_dt).total_seconds() / 60.0
                print(f"[LATE] {rec.employee_id.name} | Scheduled: {start_dt.time()} | "
                      f"Check-in: {rec.check_in.time()} | Late by {rec.late_arrival:.0f} min")
            else:
                rec.is_late = False
                rec.late_arrival = 0.0
                print(f"[ON-TIME] {rec.employee_id.name} arrived on or before grace period.")

    def _apply_late_deduction(self):
        """Deduct 1 Annual Leave on every 4th late in a month, or 20% daily wage if leaves exhausted."""
        self.ensure_one()
        employee = self.employee_id
        if not employee:
            return

        # Monthly boundaries
        start_month = self.check_in.replace(day=1, hour=0, minute=0, second=0)
        end_month = (start_month + timedelta(days=32)).replace(day=1)

        # Count total lates in this month
        late_count = self.search_count([
            ('employee_id', '=', employee.id),
            ('is_late', '=', True),
            ('check_in', '>=', start_month),
            ('check_in', '<', end_month),
        ])

        print(f"[LATE COUNT] {employee.name} has {late_count} late(s) in {self.check_in.strftime('%B %Y')}.")

        # Deduct leave only on every 4th late (4, 8, 12, …)
        if late_count % 4 != 0:
            print(f"[NO DEDUCTION] {employee.name} late #{late_count} — no deduction this time.")
            return

        # Get annual leave type
        leave_type = self.env['hr.leave.type'].search([('name', '=', 'Annual Leave')], limit=1)
        if not leave_type:
            print("[ERROR] 'Annual Leave' type not found — cannot deduct leave.")
            return

        # Check available annual leave balance
        remaining_leaves = employee.remaining_leaves or 0
        print(f"[LEAVE BALANCE] {employee.name} has {remaining_leaves} remaining annual leave(s).")

        if remaining_leaves > 0:
            # Deduct 1 day annual leave
            leave = self.env['hr.leave'].create({
                'name': 'Auto Deduction - Late Arrival',
                'employee_id': employee.id,
                'holiday_status_id': leave_type.id,
                'request_date_from': self.check_in.date(),
                'request_date_to': self.check_in.date(),
                'number_of_days': 1,
                'state': 'validate',
            })
            print(f"[LEAVE DEDUCTED] 1 Annual Leave created for {employee.name} "
                  f"(Late #{late_count}). Record ID: {leave.id}")
        else:
            # No leaves left — deduct 20% of basic daily salary
            contract = employee.contract_id
            if not contract or not contract.wage:
                print(f"[ERROR] {employee.name} has no active contract or wage not set — cannot deduct salary.")
                return

            daily_salary = contract.wage / 30
            deduction_amount = daily_salary * 0.20
            print(f"[SALARY DEDUCTION] {employee.name} | Basic: {contract.wage} | "
                  f"Daily: {daily_salary:.2f} | Deduction (20%): {deduction_amount:.2f}")

            # Record the deduction for HR review (you can create a custom model for logs)
            self.env['ir.logging'].create({
                'name': f"Late Deduction - Salary",
                'type': 'server',
                'dbname': self._cr.dbname,
                'level': 'INFO',
                'message': f"20% daily salary ({deduction_amount:.2f}) deducted for {employee.name} "
                           f"(no annual leave balance).",
                'path': __name__,
                'line': '0',
                'func': '_apply_late_deduction'
            })
