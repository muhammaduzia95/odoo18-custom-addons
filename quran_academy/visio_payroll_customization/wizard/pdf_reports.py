from email.policy import default

from odoo import models, fields, api
from datetime import datetime, timedelta


class PdfReportsWizard(models.TransientModel):
    _name = "pdf.reports.wizard"
    _description = "PDF Reports Wizard"

    def _default_month(self):
        """Returns the first day of the current month."""
        return datetime.today().replace(day=1)

    month = fields.Date(string="Month", required=True, default=_default_month)

    report_type = fields.Selection([
        ('pay_bank', 'Pay Receiving Bank List'),
        ('pay_cash', 'Pay Receiving Cash List'),
        ('salary_summary', 'Salary Summary'),
        ('pay_bank_sheet', 'Pay Receiving Bank Sheet'),
        ('pay_cash_sheet', 'Pay Receiving Cash Sheet'),
        ('payroll_sheet', 'Payroll Sheet'),
        ('eobi_anjuman', 'EOBI Anjuman'),
        ('eobi_maktaba', 'EOBI Maktaba'),
    ], string="Select Report Type", required=True, default='payroll_sheet')

    def action_print_report(self):
        """ Generate PDF report based on selected radio button """
        data = {
            'month': self.month,
        }

        report_mapping = {
            'pay_bank': 'visio_payroll_customization.pay_receiving_list_report_action',
            'pay_cash': 'visio_payroll_customization.pay_receiving_cash_list_report_action',
            'salary_summary': 'visio_payroll_customization.salary_summary_report_action',
            'pay_bank_sheet': 'visio_payroll_customization.pay_receiving_bank_sheet_report_action',
            'pay_cash_sheet': 'visio_payroll_customization.pay_receiving_cash_sheet_report_action',
            'payroll_sheet': 'visio_payroll_customization.payroll_sheet_report_action',
            'eobi_anjuman': 'visio_payroll_customization.eobi_anjuman_report_action',
            'eobi_maktaba': 'visio_payroll_customization.eobi_maktaba_report_action',
        }

        selected_report = report_mapping.get(self.report_type)
        if selected_report:
            return self.env.ref(selected_report).report_action(self, data=data)
        else:
            return False

    def action_salary_summary(self):
        return self.env.ref('visio_payroll_customization.action_salary_summary').sudo().read()[0]

    def action_payroll_sheet(self):
        return self.env.ref('visio_payroll_customization.action_payroll_sheet_qa').sudo().read()[0]
