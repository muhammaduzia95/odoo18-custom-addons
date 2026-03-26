# quran_academy\visio_payroll_customization\report\eobi_anjuman_report.py
from odoo import models, fields, api
from datetime import timedelta


class EobiAnjumanReport(models.AbstractModel):
    _name = "report.visio_payroll_customization.eobi_anjuman_report_template"
    _description = "EOBI Anjuman Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        month = fields.Date.from_string(data['month'])
        month_start = month.replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', month_start),
            ('date_to', '<=', month_end),
            # ('state', '=', 'done'),
            ('emp_eobi', '>', 0),
            ('eobi_worker', '>', 0),
            ('master_department', '=', 'Markazi Anjuman')
        ])
        print("payslips", len(payslips))

        # Sort numerically by worker_code if possible
        payslips_sorted = sorted(payslips,key=lambda p: int(p.worker_code)
        if (p.worker_code or "").isdigit() else float('inf'))

        return {
            'doc_ids': [p.id for p in payslips_sorted],
            'doc_model': 'hr.payslip',
            'docs': payslips_sorted,
            'month': month.strftime('%B - %Y'),
        }
