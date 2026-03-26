from odoo import models, fields, api, Command
from odoo.osv import expression

class ResPartner(models.Model):
    _inherit = 'res.partner'


    discount_percent = fields.Float(
        string='Discount Percentage',
        default=0.0,
        help="Default discount percentage allowed to this user"
    )


