# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_so_customize\models\account_move.py
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError, UserError , AccessError

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id', 'invoice_line_ids')
    def _onchange_partner_id_apply_taxes(self):
        """Apply purchase_taxes from res.partner to all invoice lines when partner_id is changed."""
        for move in self:
            if move.partner_id and move.move_type == 'out_invoice':
                for line in move.invoice_line_ids:
                    line.tax_ids = [(6, 0, (line.tax_ids.ids + move.partner_id.sales_taxes.ids))]

            elif move.partner_id and move.move_type == 'in_invoice':
                for line in move.invoice_line_ids:
                    line.tax_ids = [(6, 0, (line.tax_ids.ids + move.partner_id.purchase_taxes.ids))]

    def unlink(self):
        for rec in self:
            if rec.move_type == 'out_invoice':
                if not self.env.user.has_group('visio_tti_so_customize.group_delete_customer_invoice'):
                    raise AccessError(_("You are not allowed to delete Customer Invoices."))

            elif rec.move_type == 'in_invoice':
                if not self.env.user.has_group('visio_tti_so_customize.group_delete_vendor_bills'):
                    raise AccessError(_("You are not allowed to delete Vendor Bills."))

            elif rec.move_type == 'entry':
                if not self.env.user.has_group('visio_tti_so_customize.group_delete_journal_entries'):
                    raise AccessError(_("You are not allowed to delete Journal Entries."))

        return super(AccountMove, self).unlink()


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def unlink(self):
        for payment in self:
            if payment.payment_type == 'inbound':
                if not self.env.user.has_group('visio_tti_so_customize.group_delete_customer_payments'):
                    raise AccessError(_("You are not allowed to delete Customer Payments."))
            elif payment.payment_type == 'outbound':
                if not self.env.user.has_group('visio_tti_so_customize.group_delete_vendor_payments'):
                    raise AccessError(_("You are not allowed to delete Vendor Payments."))

        return super(AccountPayment, self).unlink()
