# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_payment_journal_report\models\inherit_account_payment.py
from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_category = fields.Selection([
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Transfer')
    ], string="Payment Mode")

    cash_reference = fields.Char(string="Cash")
    cheque_number = fields.Char(string="Cheque Number")
    online_transaction_id = fields.Char(string="Online Transfer")

