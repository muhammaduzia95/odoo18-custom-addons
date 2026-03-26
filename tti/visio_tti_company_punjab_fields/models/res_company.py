from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    bank_name = fields.Char(string="Bank Name")
    account_title = fields.Char(string="Account Title")
    swift_code = fields.Char(string="SWIFT Code")
    branch_code = fields.Char(string="Branch Code")
    account_no = fields.Char(string="Account Number")
    iban = fields.Char(string="IBAN")
