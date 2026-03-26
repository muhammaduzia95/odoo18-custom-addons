from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_posted_invoice = fields.Boolean(
        string="Has Posted Invoice",
        default=False
    )
