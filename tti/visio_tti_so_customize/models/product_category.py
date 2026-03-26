from odoo import models, fields, api, Command
from odoo.osv import expression


class ProductCategory(models.Model):
    _inherit = 'product.category'

    code = fields.Char(string='Product Category Code', copy=False, readonly=True)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:

            existing_codes = self.search([]).mapped('code')
            numeric_codes = [int(code) for code in existing_codes if code and code.isdigit()]
            next_code = str(max(numeric_codes) + 1) if numeric_codes else '1'
            vals['code'] = next_code

        return super(ProductCategory, self).create(list_vals)
