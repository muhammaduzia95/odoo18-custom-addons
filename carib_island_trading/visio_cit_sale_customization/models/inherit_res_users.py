# carib_island_trading\visio_cit_sale_customization\models\inherit_res_users.py
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_salesperson = fields.Boolean(string="Is Salesperson")

