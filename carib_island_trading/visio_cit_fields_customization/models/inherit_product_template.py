from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    size = fields.Char(string='Size')
    cit_case_qty = fields.Integer(string='Case Quantity')
