from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError

class HrContract(models.Model):
    _inherit = 'hr.contract'

    loan_recovery = fields.Float(digits="Payroll", string="Loan Recovery", default=0, currency_field='currency_id')

    loan_recovery_source = fields.Selection(
        [('contract', 'Contract'), ('payslip', 'Payslip')],
        string="Loan Recovery Source",
        default='contract'
    )
    wage_source = fields.Selection(
        [('contract', 'Contract'), ('payslip', 'Payslip')],
        string="Wage Source",
        default='contract'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='company_id.currency_id'
    )

    def write(self, vals):
        if 'loan_recovery' in vals:
            vals['loan_recovery_source'] = 'contract'
        if 'wage' in vals:
            vals['wage_source'] = 'contract'
        return super(HrContract, self).write(vals)

