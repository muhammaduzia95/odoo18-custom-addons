from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    po_company_image = fields.Image(string="Purchase Order Image")
