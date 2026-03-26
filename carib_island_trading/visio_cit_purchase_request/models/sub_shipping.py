# carib_island_trading\visio_cit_purchase_request\models\sub_shipping.py
from odoo import models, fields


class SubShipping(models.Model):
    _name = 'sub.shipping'
    _description = 'Sub Shipping'

    name = fields.Char(string='Sub Method', required=True)
    shipping_method_id = fields.Many2one(
        'shipping.methods',
        string='Main Shipping Method',
        required=True,
        ondelete='cascade'
    )