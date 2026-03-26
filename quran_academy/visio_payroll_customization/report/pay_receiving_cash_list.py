from odoo import models, api, fields
from datetime import datetime, timedelta

class PayReceivingList(models.AbstractModel):
    _name = "report.visio_payroll_customization.pay_cash_list_template"
    _description = "Pay Receiving Cash List"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Fetches employee payslips for the selected month in the wizard.
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
        print("payslips : " , payslips)

        return {
            'doc_ids': payslips.ids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'month': month.strftime('%B %Y'),
        }
