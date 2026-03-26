# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\inherit_sale_order.py
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_po_no = fields.Char(string="Customer P.O. No.")
    customer_po_date = fields.Date(string="Customer P.O. Date")
    ship_date = fields.Date(string="Ship Date")
