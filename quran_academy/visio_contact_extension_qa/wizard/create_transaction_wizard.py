# quran_academy\visio_contact_extension_qa\wizard\create_transaction_wizard.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CreateTransactionWizard(models.TransientModel):
    _name = 'create.transaction.wizard'
    _description = 'Create Transaction Wizard'

    tran_members = fields.Many2one(
        'res.partner', string='Member', required=True
    )
    tran_date = fields.Date(string='Date', required=True)
    tran_amount = fields.Integer(string='Amount', required=True)
    tran_paid_by = fields.Char(string='Paid By')

    # Positive amount
    @api.constrains('tran_amount')
    def _check_tran_amount_positive(self):
        for rec in self:
            if rec.tran_amount <= 0:
                raise ValidationError("The amount must be greater than 0.")

    # Button: Create payment + update partner
    def action_create(self):
        self.ensure_one()

        journal = self.env['account.journal'].sudo().search([('type', '=', 'cash')], limit=1)
        if not journal:
            raise ValidationError("No Cash journal found. Configure one in Accounting ▸ Configuration ▸ Journals.")

        # 1) create the payment
        payment = self.env['account.payment'].sudo().create({
            'partner_id': self.tran_members.id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'journal_id': journal.id,
            'amount': self.tran_amount,
            'memo': self.tran_paid_by or '',
            'date': self.tran_date,
            'election_member': True,
        })

        # confirm the payment
        payment.sudo().action_post()

        # Payment number from account.payment
        receipt_no = payment.name

        # 2) update partner custom fields
        self.tran_members.sudo().write({
            'trans_date_qa': self.tran_date,
            'paid_by_qa'   : self.tran_paid_by,
            'mlcontb'      : self.tran_amount,
            'rec_no_qa'    : receipt_no,
        })

        return {'type': 'ir.actions.act_window_close'}
