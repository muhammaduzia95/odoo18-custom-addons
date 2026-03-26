from odoo import models, api, fields
from datetime import datetime, timedelta

class PayReceivingList(models.AbstractModel):
    _name = "report.visio_payroll_customization.pay_receiving_list_template"
    _description = "Pay Receiving List"

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
            ('paid_by', 'in', ['cross_cheque', 'deposited_in_bank'])
        ])

        # Sort payslips
        # 1) first_child_dep (string) alphabetically
        # 2) paid_by: cross_cheque first
        # 3) employee name alphabetically
        payslips = payslips.sorted(
            key=lambda p: (
                p.first_child_dep or "",  # sort departments alphabetically
                0 if p.paid_by == 'cross_cheque' else 1,  # cross_cheque first
                p.employee_id.name.lower()  # sort employee name
            )
        )
        print("payslips : " , payslips)


        return {
            'doc_ids': payslips.ids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'month': month.strftime('%B %Y'),
        }
