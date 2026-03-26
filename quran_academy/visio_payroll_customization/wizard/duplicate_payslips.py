from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class DuplicatePayslips(models.TransientModel):
    _name = 'duplicate.payslips.wizard'
    _description = 'Duplicate Payslips Wizard'

    def _default_date_from(self):
        """Returns the first day of the previous month."""
        today = datetime.today()
        first_day_this_month = today.replace(day=1)
        last_month = first_day_this_month - timedelta(days=1)
        return last_month.replace(day=1)

    def _default_new_date_from(self):
        """Returns the first day of the current month."""
        return datetime.today().replace(day=1)

    date_from = fields.Date(string="Previous Month", required=True, default=_default_date_from)
    new_date_from = fields.Date(string="Current Month", required=True, default=_default_new_date_from)

    def action_duplicate_payslips(self):
        """Duplicate payslips for the selected month with updated dates."""
        try:
            self.ensure_one()

            # if self.new_date_from < self.date_from:
                # raise ValidationError("⚠ The new month cannot be earlier than the original month!")

            original_month_start = self.date_from.replace(day=1)
            next_month = self.date_from.replace(day=28) + timedelta(days=4)
            original_month_end = next_month.replace(day=1) - timedelta(days=1)

            new_month_start = self.new_date_from.replace(day=1)
            next_new_month = self.new_date_from.replace(day=28) + timedelta(days=4)
            new_month_end = next_new_month.replace(day=1) - timedelta(days=1)

            payslips = self.env['hr.payslip'].search([
                ('date_from', '>=', original_month_start),
                ('date_to', '<=', original_month_end),
                ('state' , 'in' , ['draft', 'done']),
                '|',
                ('employee_id.date_leaving', '=', False),
                ('employee_id.date_leaving', '>=', new_month_start),
            ])
            if not payslips:
                raise ValidationError("⚠ No draft payslips found for the selected month!")

            for payslip in payslips:
                employee_name = payslip.employee_id.name

                old_month_name = original_month_start.strftime('%B-%Y')
                new_month_name = new_month_start.strftime('%B-%Y')

                if old_month_name in payslip.name:
                    new_name = payslip.name.replace(old_month_name, new_month_name)
                else:
                    new_name = f"Salary Slip of {employee_name} for {new_month_name}"

                if payslip.employee_id.active:
                    payslip.copy({
                        'date_from': new_month_start,
                        'date_to': new_month_end,
                        'name': new_name
                    })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': 'Payslips have been successfully generated.',
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            raise ValidationError(f"Failed to process the Excel file: {str(e)}")
