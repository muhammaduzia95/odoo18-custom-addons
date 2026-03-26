
from odoo import fields, models

class HrEmployee(models.Model):
    """Extends the 'hr.employee' model to include loan_count."""
    _inherit = "hr.employee"

    loan_count = fields.Integer(
        string="Loan Count",
        help="Number of loans associated with the employee",
        compute='_compute_loan_count')

    def _compute_loan_count(self):
        """Compute the number of loans associated with the employee."""
        for rec in self:
            rec.loan_count = rec.env['hr.loan'].search_count(
                [('employee_id', '=', rec.id)])

class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    is_leave_deduct = fields.Boolean(string='Is Leave Deduct', default=False)