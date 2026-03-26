from odoo import models

class AccountMove(models.Model):
    _inherit = 'account.move'

    def create(self, vals):
        moves = super().create(vals)

        for move in moves:
            if move.move_type == 'out_invoice' and move.invoice_origin:
                sale = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
                if sale:
                    sale.has_posted_invoice = True   # now becomes True on creation

        return moves
