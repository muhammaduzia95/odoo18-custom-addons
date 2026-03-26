from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class PostPayslipsWizard(models.TransientModel):
    _name = 'post.payslips.wizard'
    _description = 'Post Payslips Wizard'

    def _default_date_from(self):
        return datetime.today().replace(day=1)

    date_from = fields.Date(string="Month", required=True, default=_default_date_from)

    def action_post_payslips(self):
        """Finds all payslips in the selected month that are in draft and posts them."""
        try:
            self.ensure_one()

            month_start = self.date_from.replace(day=1)
            next_month = self.date_from.replace(day=28) + timedelta(days=4)
            month_end = next_month.replace(day=1) - timedelta(days=1)

            payslips = self.env['hr.payslip'].search([
                ('date_from', '>=', month_start),
                ('date_to', '<=', month_end),
                ('state', '=', 'draft')
            ])

            if not payslips:
                raise ValidationError("No draft payslips found for the selected month!")

            for payslip in payslips:
                payslip.compute_sheet()
                payslip.action_payslip_done()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': 'Payslips have been successfully posted.',
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            raise ValidationError(f"Failed to process the Excel file: {str(e)}")


    def action_compute_sheets(self):
        try:
            self.ensure_one()

            month_start = self.date_from.replace(day=1)
            next_month = self.date_from.replace(day=28) + timedelta(days=4)
            month_end = next_month.replace(day=1) - timedelta(days=1)

            payslips = self.env['hr.payslip'].search([
                ('date_from', '>=', month_start),
                ('date_to', '<=', month_end),
                ('state', '=', 'draft')
            ])

            if not payslips:
                raise ValidationError("No draft payslips found for the selected month!")

            for payslip in payslips:
                payslip.compute_sheet()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': 'Payslips have been successfully computed.',
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            raise ValidationError(f"Failed to process the Excel file: {str(e)}")