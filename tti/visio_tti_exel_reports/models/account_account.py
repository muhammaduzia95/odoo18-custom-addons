from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    tti_report_type = fields.Selection(
        selection=[
            ('default', 'Default'),
            ('sale', 'Sale'),
            ('receivable', 'Receivable'),
            ('bank', 'Bank'),
            ('wht_sale', 'WHT Sale'),
            ('wht_income', 'WHT Income'),
            ('tax', 'Tax'),
        ],
        string='TTI Report Type',
        default='default'
    )