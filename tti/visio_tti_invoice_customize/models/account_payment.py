from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    multi_payment_id = fields.Many2one('account.multi.payments', string="Multi Payment")

    po_ref = fields.Char(string="PO Reference", compute="_compute_po_ref")

    @api.depends('reconciled_bills_count', 'reconciled_bill_ids')
    def _compute_po_ref(self):
        for rec in self:
            po_refs = []
            if rec.reconciled_bill_ids:
                for bill in rec.reconciled_bill_ids:
                    po_refs.append(bill.name)
                rec.po_ref = ', '.join(po_refs)
            else:
                rec.po_ref = False
