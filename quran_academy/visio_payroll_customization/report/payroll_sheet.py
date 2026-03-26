from odoo import models, fields, api
from datetime import datetime, timedelta

class PayrollSheetReport(models.AbstractModel):
    _name = "report.visio_payroll_customization.payroll_sheet_template"
    _description = "Payroll Sheet Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Fetches payslip details for the selected month.
        Filters only "Done" payslips and groups them by `first_child_dep`, then by `department`.
        """
        month = fields.Date.from_string(data['month'])
        month_start = month.replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', month_start),
            ('date_to', '<=', month_end),
            # ('state', '=', 'done'),
        ])

        grouped_data = {}

        for payslip in payslips:
            first_child_dep = payslip.first_child_dep
            department = payslip.employee_id.department_id.name

            if first_child_dep not in grouped_data:
                grouped_data[first_child_dep] = {}

            if department not in grouped_data[first_child_dep]:
                grouped_data[first_child_dep][department] = []

            grouped_data[first_child_dep][department].append(payslip)

        return {
            'doc_ids': payslips.ids,
            'doc_model': 'hr.payslip',
            'docs': grouped_data,
            'month': month.strftime('%B %Y'),
        }
