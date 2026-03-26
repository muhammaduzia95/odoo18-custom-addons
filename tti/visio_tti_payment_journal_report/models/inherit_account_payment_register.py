# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_payment_journal_report\models\inherit_account_payment_register.py
from odoo import models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    payment_category_pr = fields.Selection([
        ('cash_pr', 'Cash'),
        ('cheque_pr', 'Cheque'),
        ('online_pr', 'Online Transfer')
    ], string="Payment Mode")

    cash_reference_pr = fields.Char(string="Cash")
    online_transaction_id_pr = fields.Char(string="Online Transfer")
    cheque_number_pr = fields.Char(string="Cheque Number")

    def _create_payment_vals_from_wizard(self, batch_result=None):
        vals = super()._create_payment_vals_from_wizard(batch_result=batch_result)
        print("vals", vals)

        # Map wizard selection → payment selection
        category_map = {
            'cash_pr': 'cash',
            'cheque_pr': 'cheque',
            'online_pr': 'online',
        }
        print("category_map", category_map)

        vals.update({
            'payment_category': category_map.get(self.payment_category_pr),
            'cash_reference': self.cash_reference_pr,
            'cheque_number': self.cheque_number_pr,
            'online_transaction_id': self.online_transaction_id_pr,
        })
        print("vals.update", vals.update)

        return vals
