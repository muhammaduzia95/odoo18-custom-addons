# quran_academy\visio_contact_extension_qa\models\inherit_account_payment.py
from odoo import models, fields, api

class AccPayment(models.Model):
    _inherit = 'account.payment'

    election_member = fields.Boolean(string="Is Election Member")
