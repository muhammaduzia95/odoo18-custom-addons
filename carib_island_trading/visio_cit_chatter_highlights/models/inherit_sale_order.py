from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_unread_chatter = fields.Boolean(string="Has Unread Chatter")

    def read(self, fields=None, load='_classic_read'):
        print("self.ids:", self.ids)
        print(f"📖 read() called for Sale Order(s): {[so.name for so in self]}")

        result = super().read(fields=fields, load=load)

        # Reset only if a single SO is being opened (form view)
        if len(self) == 1 and self.has_unread_chatter:
            print(f"✅ Resetting has_unread_chatter for: {self.name}")
            self.sudo().write({'has_unread_chatter': False})
        else:
            print("ℹ️ Skipping reset (either multiple SOs or no unread flag)")

        return result

    # def read(self, fields=None, load='_classic_read'):
    #     print("self:", self)
    #     print(f"📖 read() called for Sale Order(s): {[so.name for so in self]}")
    #     result = super().read(fields=fields, load=load)
    #     to_reset = self.filtered(lambda so: so.has_unread_chatter)
    #     if to_reset:
    #         print(f"🟦 Resetting has_unread_chatter for: {[so.name for so in to_reset]}")
    #         to_reset.sudo().write({'has_unread_chatter': False})
    #     else:
    #         print("ℹ️ No Sale Orders to reset.")
    #
    #     return result


