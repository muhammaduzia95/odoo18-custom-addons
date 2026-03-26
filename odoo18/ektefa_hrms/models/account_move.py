
from odoo import models, fields, api


class Invoice(models.Model):
    _inherit = 'account.move'

    ektefa_employee_id = fields.Char(string='Ektefa Employee ID')
    ektefa_employee_name = fields.Char(string='Ektefa Employee Name')

    def unlink(self):
        move_ids = self.ids
        ektefa_payrun = self.env['ektefa.payrun'].search([('move_id', 'in', move_ids)])
        ektefa_loan_settlement = self.env['ektefa.loans.settlement'].search([('move_id', 'in', move_ids)])
        ektefa_loan = self.env['ektefa.loans'].search([('move_id', 'in', move_ids)])
        ektefa_eos = self.env['ektefa.end.of.service'].search([('move_id', 'in', move_ids)])
        res = super(Invoice, self).unlink()
        if len(ektefa_payrun) > 0:
            ektefa_payrun.unlink()
        if len(ektefa_loan) > 0:
            ektefa_loan.unlink()
        if len(ektefa_loan_settlement) > 0:
            ektefa_loan_settlement.unlink()
        if len(ektefa_eos) > 0:
            ektefa_eos.unlink()
        return res

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ektefa_employee_id = fields.Char(string='Ektefa Employee ID')
