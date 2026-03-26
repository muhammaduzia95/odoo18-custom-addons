from datetime import datetime
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def create(self, vals):
        payslip = super().create(vals)
        payslip.mapped('worked_days_line_ids')._invalidate_cache(['amount'])
        return payslip

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        work_hours = self.contract_id.get_work_hours(self.date_from, self.date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0

        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            if work_entry_type.name == 'Overtime Hours':
                continue

            days = round(hours / hours_per_day, 5) if hours_per_day else 0

            if work_entry_type_id == biggest_work:
                days += add_days_rounding

            day_rounded = self._round_days(work_entry_type, days)
            add_days_rounding += (days - day_rounded)

            attendance_line = {
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_type_id,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }

            contract_start = self.contract_id.date_start
            contract_end = self.contract_id.date_end or self.date_to

            # Calculate the effective date range (intersection of payslip period and contract period)
            effective_start = max(self.date_from, contract_start)
            effective_end = min(self.date_to, contract_end)

            has_out_of_contract = any(
                line.work_entry_type_id.code == 'OUT'
                for line in self.worked_days_line_ids
            )

            # if not has_out_of_contract and contract_start > self.date_from:
            #     out_of_contract_work_entry_type = self.env['hr.work.entry.type'].search([
            #         ('code', '=', 'OUT')
            #     ], limit=1)
            #
            #     if out_of_contract_work_entry_type:
            #         # Calculate days from date_from to contract_start (excluding Sundays)
            #         out_days = 0
            #         current_date = self.date_from
            #         while current_date < contract_start:
            #             if current_date.weekday() != 6:  # Not Sunday
            #                 out_days += 1
            #             current_date += timedelta(days=1)
            #
            #         # Add OUT line at the beginning
            #         res.append({
            #             'sequence': out_of_contract_work_entry_type.sequence,
            #             'work_entry_type_id': out_of_contract_work_entry_type.id,
            #             'number_of_days': out_days,
            #             'number_of_hours': 0,
            #         })

            if self.contract_id.work_entry_source == "calendar" and work_entry_type.name == 'Attendance':
                if contract_start > self.date_from:
                    sundays = sum(
                        1 for d in range(effective_start.day, effective_end.day + 1)
                        if date(effective_start.year, effective_start.month, d).weekday() == 6
                    )
                else:
                    year = self.date_from.year
                    month = self.date_from.month
                    total_days_in_month = monthrange(year, month)[1]
                    sundays = sum(
                        1 for d in range(1, total_days_in_month + 1)
                        if date(year, month, d).weekday() == 6
                    )

                attendance_line['number_of_days'] += sundays

            if self.contract_id.work_entry_source == "attendance" and work_entry_type.name == 'Attendance':
                attendance_model = self.env["hr.attendance"]
                attendance_recs = attendance_model.search([
                    ("employee_id", "=", self.employee_id.id),
                    ("check_in", ">=", self.date_from),
                    ("check_in", "<=", self.date_to),
                ])

                # Filter out Sundays from attendance records
                attendance_recs = attendance_recs.filtered(
                    lambda att: att.check_in.weekday() != 6  # 6 = Sunday
                )

                # Calculate Sundays only within the effective contract period
                if contract_start > self.date_from:
                    sundays = sum(
                        1 for d in range(effective_start.day, effective_end.day + 1)
                        if date(effective_start.year, effective_start.month, d).weekday() == 6
                    )
                else:
                    # Original logic for full month
                    year = self.date_from.year
                    month = self.date_from.month
                    total_days_in_month = monthrange(year, month)[1]
                    sundays = sum(
                        1 for d in range(1, total_days_in_month + 1)
                        if date(year, month, d).weekday() == 6
                    )

                print("------ ATTENDANCE RECORDS ------")
                print("Employee:", self.employee_id.name)
                print("Date From:", self.date_from)
                print("Date To:", self.date_to)

                day_hours = {}
                for att in attendance_recs:
                    print("\nAttendance Record Found →", att.id)
                    print("Check In:", att.check_in, "Check Out:", att.check_out)

                    if not att.check_out:
                        print("Skipping → No check_out")
                        continue

                    day = att.check_in.date()
                    worked_hours = (att.check_out - att.check_in).total_seconds() / 3600.0
                    print("Raw Worked Hours on", day, "=", worked_hours)

                    # -------------------------------
                    # SUBTRACT LUNCH ONLY IF OVERLAP
                    # -------------------------------
                    lunch_duration = 0.0
                    calendar = self.contract_id.resource_calendar_id

                    if calendar:
                        lunch_line = calendar.attendance_ids.filtered(
                            lambda l: l.dayofweek == str(att.check_in.weekday()) and l.day_period == "lunch"
                        )

                        if lunch_line:
                            lunch_from = lunch_line[0].hour_from
                            lunch_to = lunch_line[0].hour_to

                            # Convert attendance check-in/check-out into float hours
                            att_start = att.check_in.hour + (att.check_in.minute / 60)
                            att_end = att.check_out.hour + (att.check_out.minute / 60)

                            print(f"Lunch break: {lunch_from} → {lunch_to}")
                            print(f"Attendance hours: {att_start} → {att_end}")

                            # Calculate overlap
                            overlap_start = max(att_start, lunch_from)
                            overlap_end = min(att_end, lunch_to)

                            if overlap_end > overlap_start:
                                lunch_duration = overlap_end - overlap_start
                                print("Actual lunch overlap =", lunch_duration, "hours")
                            else:
                                print("No lunch overlap → No subtraction")

                    # Apply lunch deduction based on overlap
                    worked_hours -= lunch_duration
                    if worked_hours < 0:
                        worked_hours = 0

                    print("Worked Hours after lunch deduction =", worked_hours)

                    # Ensure no negative value
                    worked_hours = max(worked_hours, 0)

                    day_hours[day] = day_hours.get(day, 0) + worked_hours

                print("\n------ DAILY HOURS SUMMARY ------")
                print(day_hours)

                total_attendance_days = 0.0
                for day, hours in day_hours.items():
                    if hours > 4:
                        print(day, "→ FULL DAY (Hours:", hours, ")")
                        total_attendance_days += 1
                    elif 3 <= hours < 4:
                        print(day, "→ HALF DAY (Hours:", hours, ")")
                        total_attendance_days += 0.5
                    else:
                        print(day, "→ ABSENT (Hours:", hours, ")")

                print("\nTotal Attendance Days (before Sundays):", total_attendance_days)
                # print("Sundays Count:", sundays)

                # total_attendance_days = len(attendance_recs)
                total_days = total_attendance_days + sundays
                attendance_line['number_of_days'] = total_days

                print("FINAL number_of_days:", total_days)
                print("------------------------------------")

            res.append(attendance_line)

        employee = self.employee_id
        # if employee:
        #     attendance_model = self.env["hr.attendance"]
        #     year = self.date_from.year
        #     month = self.date_from.month
        #     total_days_in_month = monthrange(year, month)[1]
        #     gross_salary = getattr(self.contract_id, "wage", 0.0) or 0.0
        #     daily_salary = gross_salary / total_days_in_month if total_days_in_month else 0.0
        #
        #     # 🧩 Combine both Late and Single Clock logic
        #     deduction_rules = [
        #         {
        #             "name": "Late Arrival",
        #             "domain": [
        #                 ("employee_id", "=", employee.id),
        #                 ("check_in", ">=", self.date_from),
        #                 ("check_in", "<=", self.date_to),
        #                 ("late", "=", True),
        #                 ("late_deduction_done", "=", False),
        #             ],
        #             "block_size": 4,
        #             "code": "LAD",
        #             "field_to_update": "late_deduction_done",
        #         },
        #         {
        #             "name": "Single Clock",
        #             "domain": [
        #                 ("employee_id", "=", employee.id),
        #                 ("check_in", ">=", self.date_from),
        #                 ("check_in", "<=", self.date_to),
        #                 ("auto_checkout", "=", True),
        #                 ("auto_entry_deduction", "=", False),
        #             ],
        #             "block_size": 5,
        #             "code": "SCD",
        #             "field_to_update": "auto_entry_deduction",
        #         },
        #     ]
        #
        #     for rule in deduction_rules:
        #         records = attendance_model.search(rule["domain"], order="check_in asc")
        #         records = records.filtered(lambda a: a.check_in.weekday() != 6)
        #         rec_count = len(records)
        #         print(f"⚙️ Found {rec_count} {rule['name']} records for {employee.name}")
        #
        #         if rec_count >= rule["block_size"]:
        #             # Calculate deduction blocks (grouped)
        #             deduction_blocks = rec_count // rule["block_size"]
        #             processed_records = records[:deduction_blocks * rule["block_size"]]
        #             # processed_records.write({rule["field_to_update"]: True})
        #
        #             deduction_amount = deduction_blocks * (0.2 * daily_salary)
        #             print(f"🧾 {deduction_blocks} block(s) of {rule['name']} → -{deduction_amount:.2f}")
        #
        #             work_type = self.env["hr.work.entry.type"].search([("code", "=", rule["code"])], limit=1)
        #             if work_type:
        #                 res.append({
        #                     "sequence": work_type.sequence or 100,
        #                     "work_entry_type_id": work_type.id,
        #                     "number_of_days": 0.0,
        #                     "number_of_hours": 0.0,
        #                     "amount": -deduction_amount,
        #                 })
        #                 print(
        #                     f"✅ Added {rule['code']} line for {employee.name} → {deduction_blocks} blocks, -{deduction_amount:.2f}")
        #             else:
        #                 print(f"⚠️ Work entry type '{rule['code']}' not found — skipping deduction line")
        #
        #     sandwich_model = self.env["hr.sandwich.leave"]
        #     sandwich_records = sandwich_model.search([
        #         ("employee_id", "=", employee.id),
        #         ("date", ">=", self.date_from),
        #         ("date", "<=", self.date_to),
        #     ])
        #
        #     sandwich_count = len(sandwich_records)
        #     if sandwich_count:
        #         print(f"🥪 Found {sandwich_count} Sandwich Leave Deduction record(s) for {employee.name}")
        #
        #         total_deduction = sandwich_count * daily_salary
        #
        #         work_type = self.env["hr.work.entry.type"].search([("code", "=", "SLD")], limit=1)
        #         if work_type:
        #             res.append({
        #                 "sequence": work_type.sequence or 120,
        #                 "work_entry_type_id": work_type.id,
        #                 "number_of_days": 0.0,
        #                 "number_of_hours": 0.0,
        #                 "amount": -total_deduction,
        #             })
        #             print(f"✅ Added SLD line for {employee.name} → {sandwich_count} day(s), -{total_deduction:.2f}")
        #         else:
        #             print("⚠️ Work entry type 'SLD' not found — skipping Sandwich Leave Deduction line")

        # Sort by Work Entry Type sequence
        work_entry_type = self.env['hr.work.entry.type']
        return sorted(res, key=lambda d: work_entry_type.browse(d['work_entry_type_id']).sequence)

    def compute_sheet(self):
        for payslip in self:
            contract = payslip.contract_id
            employee = contract.employee_id if contract else payslip.employee_id
            if not contract:
                continue

            loans_advances = self.env['hr.loan'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'approve'),
                ('balance_amount', '>', 0)
            ])
            for loan in loans_advances:
                for loan_line in loan.loan_lines:
                    if (
                            payslip.date_from <= loan_line.date <= payslip.date_to
                            and not loan_line.paid
                    ):
                        if loan.type == 'loan':
                            input_code = 'SLO' if loan.loan_type == 'short' else 'CLO'
                        else:
                            input_code = 'AD'

                        existing_input = payslip.input_line_ids.filtered(
                            lambda l: l.code == input_code and l.loan_line_id == loan_line
                        )
                        if not existing_input:
                            payslip_input_type = self.env['hr.payslip.input.type'].search(
                                [('code', '=', input_code)], limit=1)
                            if not payslip_input_type:
                                raise ValueError(f"No input type found for code '{input_code}'")

                            self.env['hr.payslip.input'].create({
                                'payslip_id': payslip.id,
                                'input_type_id': payslip_input_type.id,
                                'name': 'Loan Installment' if loan.type == 'loan' else 'Advance Deduction',
                                'code': input_code,
                                'amount': loan_line.amount,
                                'contract_id': contract.id,
                                'loan_line_id': loan_line.id,
                            })

        res = super(HrPayslip, self).compute_sheet()
        return res

    def action_payslip_done(self):
        """Mark loan/advance lines paid and update totals"""
        for payslip in self:
            contract = payslip.contract_id
            employee = contract.employee_id if contract else payslip.employee_id
            if not contract:
                continue

            year = payslip.date_from.year
            month = payslip.date_from.month
            total_days_in_month = monthrange(year, month)[1]

            # Skip validation if contract starts after 1st of the month
            # if (
            #         contract.date_start
            #         and contract.date_start.year == year
            #         and contract.date_start.month == month
            #         and contract.date_start.day > 1
            # ):
            #     # Skip attendance validation for new joiners
            #     pass
            # else:
            total_days_recorded = sum(payslip.worked_days_line_ids.mapped('number_of_days'))
            if total_days_recorded != total_days_in_month:
                raise ValidationError(
                    f"Attendance incomplete for {payslip.employee_id.name}. "
                    f"Total recorded days ({total_days_recorded}) do not match "
                    f"the required days in month ({total_days_in_month})."
                )

            # Mark loan lines as paid
            for input_line in payslip.input_line_ids:
                if input_line.loan_line_id:
                    input_line.loan_line_id.paid = True
                    input_line.loan_line_id.loan_id._compute_total_amount()

        return super(HrPayslip, self).action_payslip_done()

    def action_regenerate_entries_and_lines(self):
        """Regenerate work entries and refresh worked days for this payslip."""
        for slip in self:
            print(f"Regenerating work entries for {slip.name}...")
            employee = slip.employee_id
            if not employee:
                continue

            month_start = slip.date_from
            month_end = slip.date_to

            # 1. Remove all non-validated work entries for this employee in payslip period
            work_entries = self.env['hr.work.entry'].sudo().search([
                ('employee_id', '=', employee.id),
                ('date_stop', '>=', month_start),
                ('date_start', '<=', month_end),
                ('state', '!=', 'validated')
            ])
            # work_entries.write({'active': False})
            work_entries.sudo().unlink()

            # 2. Regenerate fresh work entries for that month
            new_entries = employee.sudo().generate_work_entries(month_start, month_end, True)

            # 3. Refresh payslip worked days
            slip.sudo().worked_days_line_ids.unlink()
            new_lines = slip.sudo()._get_worked_day_lines_values()

            has_out_of_contract = any(
                line.get('work_entry_type_id') and
                self.env['hr.work.entry.type'].browse(line['work_entry_type_id']).code == 'OUT'
                for line in new_lines
            )
            contract_start = self.contract_id.date_start
            contract_end = self.contract_id.date_end or self.date_to
            if not has_out_of_contract and contract_start > self.date_from:
                out_of_contract_work_entry_type = self.env['hr.work.entry.type'].search([
                    ('code', '=', 'OUT')
                ], limit=1)

                if out_of_contract_work_entry_type:
                    out_days = 0
                    current_date = self.date_from
                    while current_date < contract_start:
                        # if current_date.weekday() != 6:  # exclude Sundays
                        out_days += 1
                        current_date += timedelta(days=1)

                    new_lines.append({
                        'sequence': out_of_contract_work_entry_type.sequence,
                        'work_entry_type_id': out_of_contract_work_entry_type.id,
                        'number_of_days': out_days,
                        'number_of_hours': 0,
                    })

            slip.sudo().write({
                'worked_days_line_ids': [(0, 0, vals) for vals in new_lines]
            })

        return True


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    amount = fields.Monetary(string='Amount', compute='_compute_amount', store=False, copy=True)

    @api.depends('is_paid', 'is_credit_time', 'number_of_hours', 'number_of_days',
                 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        for worked_days in self:
            payslip = worked_days.payslip_id
            contract = worked_days.contract_id

            # Skip invalid or unpaid lines
            if not contract or worked_days.code == 'LEAVE90' or worked_days.is_credit_time:
                worked_days.amount = 0
                continue

            # ===============================================================
            # 🟢 MAIN CUSTOM LOGIC — Monthly + Attendance-based Contracts
            # ===============================================================
            if contract.work_entry_source == 'attendance' and payslip.wage_type == "monthly":
                year = payslip.date_from.year
                month = payslip.date_from.month
                total_days_in_month = monthrange(year, month)[1]
                daily_wage = contract.gross_salary_tti / total_days_in_month
                print("daily_wage", daily_wage)
                print("total_days_in_month", total_days_in_month)
                print("contract.gross_salary_tti", contract.gross_salary_tti)
                print("contract.wage", contract.wage)
                # daily_wage = contract.wage / total_days_in_month

                if worked_days.code == 'WORK100':
                    total_days_paid = worked_days.number_of_days
                    worked_days.amount = (
                            daily_wage * total_days_paid
                    )
                    print("worked_days.amount", worked_days.amount)

                elif worked_days.code in ['LEAVE110', 'LEAVE111', 'LEAVE112']:
                    worked_days.amount = (
                        daily_wage * worked_days.number_of_days if worked_days.is_paid else 0
                    )

                elif worked_days.code == 'OUT':
                    worked_days.amount = 0.0

                # elif worked_days.code in ['LAD', 'SCD', 'SLD']:
                #     attendance_model = self.env['hr.attendance']
                #     employee = payslip.employee_id
                #     contract = payslip.contract_id
                #     year = payslip.date_from.year
                #     month = payslip.date_from.month
                #     total_days_in_month = monthrange(year, month)[1]
                #     gross_salary = getattr(contract, 'wage', 0.0) or 0.0
                #     daily_salary = gross_salary / total_days_in_month if total_days_in_month else 0.0
                #
                #     if worked_days.code in ['LAD', 'SCD']:
                #         if worked_days.code == 'LAD':
                #             domain = [
                #                 ('employee_id', '=', employee.id),
                #                 ('check_in', '>=', payslip.date_from),
                #                 ('check_in', '<=', payslip.date_to),
                #                 ('late', '=', True),
                #                 ('late_deduction_done', '=', False),
                #             ]
                #             block_size = 4
                #         else:  # SCD
                #             domain = [
                #                 ('employee_id', '=', employee.id),
                #                 ('check_in', '>=', payslip.date_from),
                #                 ('check_in', '<=', payslip.date_to),
                #                 ('auto_checkout', '=', True),
                #                 ('auto_entry_deduction', '=', False),
                #             ]
                #             block_size = 5
                #         records = attendance_model.search(domain, order='check_in asc')
                #         records = records.filtered(lambda a: a.check_in.weekday() != 6)
                #         rec_count = len(records)
                #         if rec_count >= block_size:
                #             deduction_blocks = rec_count // block_size
                #             processed_records = records[:deduction_blocks * block_size]
                #             deduction_amount = deduction_blocks * (0.2 * daily_salary)
                #             worked_days.amount = -deduction_amount
                #         else:
                #             worked_days.amount = 0.0
                #
                #     # 🧾 Sandwich Leave Deduction (SLD)
                #     elif worked_days.code == 'SLD':
                #         sandwich_model = self.env['hr.sandwich.leave']
                #         # Get number of sandwich leave deductions for employee in current month
                #         sandwich_records = sandwich_model.search([
                #             ('employee_id', '=', employee.id),
                #             ('date', '>=', payslip.date_from),
                #             ('date', '<=', payslip.date_to),
                #         ])
                #         sandwich_count = len(sandwich_records)
                #         if sandwich_count > 0:
                #             deduction_amount = sandwich_count * daily_salary
                #             worked_days.amount = -deduction_amount
                #         else:
                #             worked_days.amount = 0.0
                else:
                    # Default fallback for other line codes under attendance-based contracts
                    worked_days.amount = (
                        daily_wage * worked_days.number_of_days if worked_days.is_paid else 0
                    )

            if contract.work_entry_source == 'calendar' and payslip.wage_type == "monthly":
                year = payslip.date_from.year
                month = payslip.date_from.month
                total_days_in_month = monthrange(year, month)[1]
                daily_wage = contract.gross_salary_tti / total_days_in_month

                sundays = sum(
                    1 for d in range(1, total_days_in_month + 1)
                    if date(year, month, d).weekday() == 6
                )

                if worked_days.code == 'WORK100':
                    total_days_paid = worked_days.number_of_days
                    worked_days.amount = (
                        daily_wage * total_days_paid if worked_days.is_paid else 0
                    )

                elif worked_days.code == 'OUT':
                    worked_days.amount = 0.0

                elif worked_days.code in ['LEAVE110', 'LEAVE111', 'LEAVE112']:
                    # Leave lines: only multiply by number_of_days (no Sundays)
                    worked_days.amount = (
                        daily_wage * worked_days.number_of_days if worked_days.is_paid else 0
                    )

                else:
                    worked_days.amount = (
                        daily_wage * worked_days.number_of_days if worked_days.is_paid else 0
                    )

            # ===============================================================
            # 🟡 HOURLY WAGE LOGIC — unchanged
            # ===============================================================
            elif payslip.wage_type == "hourly":
                worked_days.amount = (
                    contract.hourly_wage * worked_days.number_of_hours
                    if worked_days.is_paid else 0
                )

    @api.depends('work_entry_type_id', 'number_of_days', 'number_of_hours', 'payslip_id')
    def _compute_name(self):
        to_check_public_holiday = {
            res[0]: res[1]
            for res in self.env['resource.calendar.leaves']._read_group(
                [
                    ('resource_id', '=', False),
                    ('work_entry_type_id', 'in', self.mapped('work_entry_type_id').ids),
                    ('date_from', '<=', max(self.payslip_id.mapped('date_to'))),
                    ('date_to', '>=', min(self.payslip_id.mapped('date_from'))),
                ],
                ['work_entry_type_id'],
                ['id:recordset']
            )
        }
        for worked_days in self:
            public_holidays = to_check_public_holiday.get(worked_days.work_entry_type_id, '')
            holidays = public_holidays and public_holidays.filtered(lambda p:
                                                                    (
                                                                            p.calendar_id.id == worked_days.payslip_id.contract_id.resource_calendar_id.id or not p.calendar_id.id)
                                                                    and p.date_from.date() <= worked_days.payslip_id.date_to
                                                                    and p.date_to.date() >= worked_days.payslip_id.date_from
                                                                    and p.company_id == worked_days.payslip_id.company_id)
            half_day = worked_days._is_half_day()
            if holidays:
                name = (', '.join(holidays.mapped('name')))
            else:
                name = worked_days.work_entry_type_id.name
            worked_days.name = name
            # worked_days.name = name + (_(' (Half-Day)') if half_day else '')


class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    def _get_duration_batch(self):
        result = {}
        cached_periods = defaultdict(float)
        for work_entry in self:
            date_start = work_entry.date_start
            date_stop = work_entry.date_stop
            if not date_start or not date_stop:
                result[work_entry.id] = 0.0
                continue
            if (date_start, date_stop) in cached_periods:
                result[work_entry.id] = cached_periods[(date_start, date_stop)]
            else:
                dt = date_stop - date_start
                duration = dt.days * 24 + dt.seconds / 3600  # Number of hours
                contract = work_entry.contract_id
                if (
                        work_entry.work_entry_type_id.name == 'Attendance'
                        and contract
                        and contract.work_entry_source == 'attendance'
                ):
                    duration = duration - 1.0 if duration > 1.0 else 0.0
                cached_periods[(date_start, date_stop)] = duration
                result[work_entry.id] = duration
        return result


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_regenerate_all_payslips(self):
        """Regenerate work entries and worked days for all payslips in this batch."""
        for batch in self:
            for slip in batch.slip_ids:
                slip.action_regenerate_entries_and_lines()
        return True

    def _validate_complete_days(self):
        """Validate that total worked days = total days in month for attendance-based monthly employees."""
        errors = []

        for payslip in self.slip_ids:
            contract = payslip.contract_id
            if not contract:
                continue

            year = payslip.date_from.year
            month = payslip.date_from.month
            total_days_in_month = monthrange(year, month)[1]

            # if contract.date_start and contract.date_start.day > 1 and contract.date_start.month == month and contract.date_start.year == year:
            #     continue

            total_days_recorded = sum(payslip.worked_days_line_ids.mapped('number_of_days'))

            if total_days_recorded != total_days_in_month:
                errors.append(
                    _(
                        f"⚠ Attendance incomplete for {payslip.employee_id.name}:\n"
                        f" - Recorded Days: {total_days_recorded}\n"
                        f" - Required Days: {total_days_in_month}\n"
                        f" - Payslip: {payslip.name or payslip.id}\n"
                    )
                )
        if errors:
            raise ValidationError(
                _("Some payslips have incomplete attendance:\n\n") + "\n".join(errors)
            )

    def action_confirm(self):
        """Intercept confirm action to validate attendance completeness."""
        self._validate_complete_days()
        return super().action_confirm()

    def action_validate(self):
        """Intercept validate action to validate attendance completeness."""
        self._validate_complete_days()
        return super().action_validate()


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def generate_work_entries(self, date_start, date_stop, force=False):
        # Call parent method to generate work entries
        new_work_entries = super().generate_work_entries(date_start, date_stop, force)

        # Filter out work entries with type code 'OVERTIME'
        overtime_entries = new_work_entries.filtered(
            lambda we: we.work_entry_type_id.code == 'OVERTIME'
        )

        if overtime_entries:
            print(f"Removing {len(overtime_entries)} overtime work entries")
            overtime_entries.unlink()
            new_work_entries = new_work_entries - overtime_entries

        return new_work_entries
