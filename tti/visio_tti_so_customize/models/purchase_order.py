from odoo import models, fields, api , _
from odoo.exceptions import ValidationError, UserError , AccessError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id' , 'order_line')
    def _onchange_partner_id_apply_taxes(self):
        """Apply purchase_taxes from res.partner to all order lines when partner_id is changed."""
        for order in self:
            if order.partner_id:
                for line in order.order_line:
                    line.taxes_id = [(6, 0, (line.taxes_id.ids + order.partner_id.purchase_taxes.ids))]

    def unlink(self):
        if not self.env.user.has_group('visio_tti_so_customize.group_delete_po'):
            raise AccessError(_("You are not allowed to delete Purchase Orders."))

        return super(PurchaseOrder, self).unlink()