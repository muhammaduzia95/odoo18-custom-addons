from odoo import models, api, fields
from datetime import datetime

class YearlySalaryReport(models.AbstractModel):
    _name = 'report.visio_payroll_customization.yearly_salary_template'
    _description = 'Yearly Salary Payslip Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        worker_code = data['worker_code']
        employee = self.env['hr.employee'].search([('employee_sequence', '=', worker_code)], limit=1)

        if not employee:
            return {
                'doc_ids': docids,
                'doc_model': 'yearly.salary.wizard',
                'docs': None,
                'employee': None,
                'payslips': [],
                'error': f"No employee found for Worker Code: {worker_code}"
            }

        current_month_start = datetime.today().replace(day=1)

        payslips = self.env['hr.payslip'].search([
            ('employee_id', '=', employee.id),
            ('date_from', '<=', current_month_start)
        ], order="date_from desc")

        return {
            'doc_ids': docids,
            'doc_model': 'yearly.salary.wizard',
            'docs': None,
            'employee': employee,
            'payslips': payslips,
            'error': None
        }
