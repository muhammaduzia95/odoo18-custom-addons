from odoo import models, fields, api
from datetime import date

class AccountMove(models.Model):
    _inherit = 'account.move'

    voucher_date = fields.Date(string='Voucher Date', compute='_compute_voucher_date', store=True)
    paid_to = fields.Char(string="Paid To")

    # cheque_no = fields.Char(string="Cheque No" , related='origin_payment_id.cheque_no')
    bill_no = fields.Char(string="Bill No" )
    instr_no = fields.Char(string="Instr No" )

    @api.depends('state')
    def _compute_voucher_date(self):
        for move in self:
            if move.state == 'posted' and not move.voucher_date:
                move.voucher_date = date.today()
