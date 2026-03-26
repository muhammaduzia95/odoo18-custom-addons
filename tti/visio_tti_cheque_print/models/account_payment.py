from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'


    is_cross = fields.Boolean(string="Is Cross Cheque" , default=False)

    def action_download_blank_pdf(self):
        self.ensure_one()
        return self.env.ref('visio_tti_cheque_print.action_report_blank_pdf').report_action(self)