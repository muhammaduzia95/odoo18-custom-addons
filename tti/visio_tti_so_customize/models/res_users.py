from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    discount_percent = fields.Float(related="partner_id.discount_percent", readonly=False)