from odoo import models, fields, api
from datetime import datetime

class EmailPayslipsWizard(models.TransientModel):
    _name = 'email.payslips.wizard'
    _description = 'Wizard to Email Payslips'

    month = fields.Date(string="Month", required=True)

    def action_send(self):
        month_start = self.month.replace(day=1)
        if month_start.month < 12:
            month_end = datetime(month_start.year, month_start.month + 1, 1)
        else:
            month_end = datetime(month_start.year + 1, 1, 1)

        payslips = self.env['hr.payslip'].search([
            ('state', '=', 'done'),
            ('date_from', '>=', month_start),
            ('date_from', '<', month_end)
        ])

        template = self.env.ref('om_hr_payroll.mail_template_payslip', raise_if_not_found=False)
        if not template:
            raise UserError("Payslip Email Template not found.")

        for slip in payslips:
            if slip.employee_id.work_email:
                template.send_mail(slip.id, force_send=True, raise_exception=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Payslips Sent',
                'message': f'Successfully sent payslips to {len(payslips)} employees.',
                'type': 'success',
                'sticky': False,
            }
        }
