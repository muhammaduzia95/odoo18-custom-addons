from odoo import models, fields


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    country_of_origin = fields.Many2one('res.country', string="Origin of Goods")
    x_studio_brand = fields.Char(string="Brand")
    x_studio_refrence = fields.Char(string="Sorting")
    x_studio_size = fields.Char(string="Size")
