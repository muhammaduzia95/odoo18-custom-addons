# carib_island_trading\visio_cit_units_qty\models\inherit_sale_order_line.py

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # units_quantity = fields.Float(string="Units Quantity", compute='_compute_units_quantity', store=True)
    #
    # @api.depends('product_uom_qty', 'product_uom')
    # def _compute_units_quantity(self):
    #     for line in self:
    #         # Use factor_inv to convert Case to Units
    #         line.units_quantity = line.product_uom_qty * (line.product_uom.factor_inv or 1.0)
