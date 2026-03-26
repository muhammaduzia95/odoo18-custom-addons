from odoo import models, api

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        message = super().create(values)

        # Trigger only for Sale Orders
        if values.get('model') == 'sale.order' and values.get('res_id'):
            sale_order = self.env['sale.order'].browse(values['res_id'])
            if sale_order.exists():
                sale_order.sudo().write({'has_unread_chatter': True})
                print(f"📬✅ Marked Sale Order {sale_order.name} as has_unread_chatter = True")

        return message
