# carib_island_trading\visio_cit_sale_customization\models\inherit_product_pricelist.py
from odoo import models, fields, api


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    assigned_user_id = fields.Many2one('res.users', string="Sales Person")

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(ProductPricelist, self).default_get(fields_list)
    #     if 'assigned_user_id' in fields_list and not res.get('assigned_user_id'):
    #         res['assigned_user_id'] = self.env.user.id
    #     return res
