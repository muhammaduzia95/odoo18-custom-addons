from odoo import models, fields, api

class WorkerPayslipWizard(models.TransientModel):
    _name = 'yearly.salary.wizard'
    _description = 'Yearly Salary Statement Worker Wizard'

    worker_code = fields.Char(string="Worker Code", required=True)

    def print_worker_payslip(self):
        print("Worker Code in Wizard:", self.worker_code)

        data = {
            'worker_code': self.worker_code,
        }
        return self.env.ref('visio_payroll_customization.worker_payslip_report_action').report_action(self, data=data)
