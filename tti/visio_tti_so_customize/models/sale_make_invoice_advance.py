from odoo import models, api


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        # Call original create_invoices logic
        invoices = super().create_invoices()

        # Loop through sale orders and apply your custom logic
        for order in self.sale_order_ids:
            order.action_lock()
            # order.hide_lock_btns = True

        return invoices
