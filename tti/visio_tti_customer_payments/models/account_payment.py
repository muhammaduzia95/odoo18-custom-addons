from odoo import models, fields, api, _

from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cheque_no = fields.Char(string="Cheque No")
    bill_no = fields.Char(string="Bill No")

    state = fields.Selection(
        selection_add=[
            ('make', 'Make'),
            ('check', 'Check')
        ],
        ondelete={
            'make': 'set default',
            'check': 'set default',
        },
    )

    def action_make(self):
        for payment in self:
            payment.state = 'make'

    def action_check(self):
        for payment in self:
            payment.state = 'check'

    @api.constrains('state', 'move_id')
    def _check_move_id(self):
        for payment in self:
            if (
                payment.state not in ('draft', 'canceled' , 'make', 'check')
                and not payment.move_id
                and payment.outstanding_account_id
            ):
                raise ValidationError(
                    _("A payment with an outstanding account cannot be confirmed without having a journal entry."))

    income_tax_wh = fields.Monetary(
        string='Income WT Tax',
        currency_field='currency_id',
        default=0.0,
        copy=False,
    )

    sal_tax_wh = fields.Monetary(
        string='Sale WT Tax',
        currency_field='currency_id',
        default=0.0,
        copy=False,
    )

    cheque_amount = fields.Monetary(
        string='Amount of cheque',
        currency_field='currency_id',
        default=0.0,
        copy=False,
    )

    sale_wh_tax_account = fields.Many2one('account.account', string="Sale WH Tax Account", copy=False, )
    income_wh_tax_account = fields.Many2one('account.account', string="Income WH Tax Account", copy=False, )

    def write(self, vals):
        reset_fields = {
            'cheque_amount': 0.0,
            'income_tax_wh': 0.0,
            'sal_tax_wh': 0.0,
            'amount': 0.0,
            'sale_wh_tax_account': None,
            'income_wh_tax_account': None,
        }
        if 'payment_type' in vals:
            vals.update(reset_fields)

        return super(AccountPayment, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'amount' in vals and not vals.get('cheque_amount'):
                vals['cheque_amount'] = vals['amount']
        return super(AccountPayment, self).create(vals_list)

    @api.onchange('cheque_amount', 'sal_tax_wh', 'income_tax_wh')
    def calculate_amount(self):
        for record in self:
            amount = record.cheque_amount + record.sal_tax_wh + record.income_tax_wh
            record.sudo().write({'amount': amount})

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        """Override to add withholding tax journal items with simplified structure"""
        # Only proceed for inbound payments with cheque amount
        if self.payment_type != 'inbound':
            return super()._prepare_move_line_default_vals(
                write_off_line_vals=write_off_line_vals,
                force_balance=force_balance
            )

        if not self.cheque_amount > 0:
            raise ValidationError("Value of cheque amount must be greater than zero")

        # Calculate total amount (cheque + withholdings)
        total_amount = self.cheque_amount + (self.income_tax_wh or 0.0) + (self.sal_tax_wh or 0.0)

        # Prepare line values list
        line_vals_list = []

        # 1. Cheque amount line (debit)
        line_vals_list.append({
            'name': f"Cheque Amount (Checque No: {self.cheque_no}, Bill No: {self.bill_no})",
            'debit': self.currency_id._convert(
                self.cheque_amount,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            ),
            'credit': 0.0,
            'partner_id': self.partner_id.id,
            'account_id': self.outstanding_account_id.id,
            'date_maturity': self.date,
        })

        # 2. Sale Withholding Tax line (if applicable)
        if self.sal_tax_wh:
            if not self.sale_wh_tax_account:
                raise UserError(_("Sale Withholding Tax Account is required when Sale WT Tax amount is set"))

            line_vals_list.append({
                'name': f"Sale Withholding Tax (Checque No: {self.cheque_no}, Bill No: {self.bill_no})",
                'debit': self.currency_id._convert(
                    self.sal_tax_wh,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                ),
                'credit': 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.sale_wh_tax_account.id,
                'date_maturity': self.date,
            })

        # 3. Income Withholding Tax line (if applicable)
        if self.income_tax_wh:
            if not self.income_wh_tax_account:
                raise UserError(_("Income Withholding Tax Account is required when Income WT Tax amount is set"))

            line_vals_list.append({
                'name': f"Income Withholding Tax (Checque No: {self.cheque_no}, Bill No: {self.bill_no})",
                'debit': self.currency_id._convert(
                    self.income_tax_wh,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                ),
                'credit': 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.income_wh_tax_account.id,
                'date_maturity': self.date,
            })

        # 4. Single Receivable line (credit for total amount)
        line_vals_list.append({
            'name': f"Receivable Amount (Checque No: {self.cheque_no}, Bill No: {self.bill_no})",
            'debit': 0.0,
            'credit': self.currency_id._convert(
                total_amount,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            ),
            'partner_id': self.partner_id.id,
            'account_id': self.destination_account_id.id,
            'date_maturity': self.date,
        })

        # Handle currency if different from company currency
        if self.currency_id != self.company_id.currency_id:
            for line in line_vals_list:
                if line['debit'] > 0:
                    line['amount_currency'] = self.amount
                    # line['amount_currency'] = self.currency_id._convert(
                    #     self.amount,
                    #     self.company_id.currency_id,
                    #     self.company_id,
                    #     self.date,
                    # )
                else:
                    line['amount_currency'] = -self.amount
                    # line['amount_currency'] = self.currency_id._convert(
                    #     -self.amount,
                    #     self.company_id.currency_id,
                    #     self.company_id,
                    #     self.date,
                    # )
                line['currency_id'] = self.currency_id.id

        # if self.cheque_no or self.bill_no:
        #     cheque_no = self.cheque_no
        #     bill_no = self.bill_no
        #     self.move_id.sudo().write({'cheque_no':cheque_no , 'bill_no':bill_no})

        return line_vals_list + (write_off_line_vals or [])

    def action_post(self):
        """Override to update journal entry after posting"""
        result = super().action_post()

        if self.move_id and (self.cheque_no or self.bill_no):
            self.move_id.sudo().write({
                'instr_no': self.cheque_no,
                'bill_no': self.bill_no
            })

        return result
