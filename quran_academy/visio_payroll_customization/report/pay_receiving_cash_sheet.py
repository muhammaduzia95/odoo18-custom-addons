from odoo import models, fields, api
from datetime import datetime, timedelta

class PayReceivingCashSheet(models.AbstractModel):
    _name = "report.visio_payroll_customization.pay_cash_sheet_template"
    _description = "Pay Receiving Cash Sheet Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Fetches payslip details for the selected month.
        Filters only "Done" payslips and those paid via Cash.
        """
        month = fields.Date.from_string(data['month'])
        month_start = month.replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', month_start),
            ('date_to', '<=', month_end),
            # ('state', '=', 'done'),
            ('paid_by', '=', 'cash')
        ])

        return {
            'doc_ids': payslips.ids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'month': month.strftime('%B %Y'),
        }
