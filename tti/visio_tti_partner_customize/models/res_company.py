from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    strn = fields.Char(string="STRN")