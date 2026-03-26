from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountPaymentRegisterInherit(models.TransientModel):
    _inherit = 'account.payment.register'

    sale_wh_tax = fields.Float(string="Sale WH Tax %")
    income_wh_tax = fields.Float(string="Income WH Tax %", default=0.0)

    sale_wh_tax_account = fields.Many2one('account.account', string="Sale WH Tax Account")
    income_wh_tax_account = fields.Many2one('account.account', string="Income WH Tax Account")

    sale_wh_tax_amount = fields.Monetary(
        compute="_compute_tax_amount", store=True
    )
    income_wh_tax_amount = fields.Monetary(
        compute="_compute_tax_amount", store=True
    )
    amount_tax = fields.Monetary(string="Total Tax Amount", store=True)

    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True)
    move_type = fields.Char(readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Fetch amount_tax and invoice_id from the invoice and set them in the wizard."""
        res = super().default_get(fields_list)
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        # if self.env.context.get('reverse_payment'):
        #     res['payment_type'] = 'outbound'
        if active_model in ['account.move', 'account.move.line'] and active_id:
            invoice = self.env['account.move'].browse(active_id)
            res.update({
                'invoice_id': invoice.id,
                'amount_tax': invoice.amount_tax or 0.0,
                'move_type': invoice.move_type,
            })
            print("invoice ", invoice.id)
            print("move_type ", invoice.move_type)
        return res

    @api.depends('sale_wh_tax', 'income_wh_tax', 'amount', 'amount_tax')
    def _compute_tax_amount(self):
        """Compute tax amounts based on percentage and total amount."""
        for record in self:
            record.sale_wh_tax_amount = ((record.sale_wh_tax * 100) / 100) * record.amount_tax
            record.income_wh_tax_amount = ((record.income_wh_tax * 100) / 100) * record.amount

    @api.onchange('sale_wh_tax', 'income_wh_tax', 'amount', 'amount_tax')
    def _onchange_tax_fields(self):
        """Trigger real-time update when tax percentage or amount changes."""
        for record in self:
            record.sale_wh_tax_amount = ((record.sale_wh_tax * 100) / 100) * record.amount_tax
            record.income_wh_tax_amount = ((record.income_wh_tax * 100) / 100) * record.amount

    # @api.constrains('sale_wh_tax', 'income_wh_tax')
    # def _check_tax_percentage(self):
    #     """Ensure the tax percentage is between 0 and 100"""
    #     for record in self:
    #         if (record.sale_wh_tax * 100) > 100:
    #             raise ValidationError("Sale WH Tax % must be less than 100.")
    #         elif (record.sale_wh_tax * 100) < 0:
    #             raise ValidationError("Sale WH Tax % must be greater than 0.")
    #         if not (0 <= (record.income_wh_tax * 100) <= 100):
    #             raise ValidationError("Income WH Tax % must be between 0 and 100.")

    def _create_payment_vals_from_wizard(self, batch_result):
        """Extend the original function while keeping write-off logic intact."""
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)

        multiplier = 1 if self.payment_type == 'inbound' else -1
        sale_wh_tax_amount = multiplier * ((self.sale_wh_tax * 100) / 100) * self.amount_tax
        income_wh_tax_amount = multiplier * ((self.income_wh_tax * 100) / 100) * self.amount

        net_amount = self.amount - (abs(sale_wh_tax_amount) + abs(income_wh_tax_amount))

        payment_vals['amount'] = abs(net_amount)

        if sale_wh_tax_amount and self.sale_wh_tax_account:
            payment_vals['write_off_line_vals'].append({
                'name': "Sale WH Tax",
                'account_id': self.sale_wh_tax_account.id,
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'amount_currency': sale_wh_tax_amount,
                'balance': self.currency_id._convert(
                    sale_wh_tax_amount,
                    self.company_id.currency_id,
                    self.company_id,
                    self.payment_date
                ),
            })

        if income_wh_tax_amount and self.income_wh_tax_account:
            payment_vals['write_off_line_vals'].append({
                'name': "Income WH Tax",
                'account_id': self.income_wh_tax_account.id,
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'amount_currency': income_wh_tax_amount,
                'balance': self.currency_id._convert(
                    income_wh_tax_amount,
                    self.company_id.currency_id,
                    self.company_id,
                    self.payment_date
                ),
            })
        return payment_vals
