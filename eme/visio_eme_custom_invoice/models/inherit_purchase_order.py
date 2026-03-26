# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\inherit_purchase_order.py
from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ship_date = fields.Date(string="Ship Date", )
