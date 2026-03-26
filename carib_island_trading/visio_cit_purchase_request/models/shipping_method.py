# \carib_island_trading\visio_cit_purchase_request\models\shipping_method.py
from odoo import models, fields


class ShippingMethod(models.Model):
    _name = 'shipping.methods'
    _description = 'Shipping Methods'

    name = fields.Char(string='Name', required=True)
