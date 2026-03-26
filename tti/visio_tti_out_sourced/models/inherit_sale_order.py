# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_out_sourced\models\inherit_sale_order.py
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    out_sourced_sample_id = fields.Many2one(
        'out.sourced.sample',
        string="Out Sourced Sample",
    )
