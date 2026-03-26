from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class AccountMultiPayments(models.Model):
    _name = 'account.multi.payments'
    _description = 'Multi Payments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True,
        default=lambda self: self.env.company)
    payment_type = fields.Selection([
        ('inbound', 'Receive'),
        ('outbound', 'Send')
    ], string='Payment Type', required=True, default='inbound')
    partner_id = fields.Many2one('res.partner', required=True)
    amount = fields.Monetary(string='Net Amount', required=True)
    sale_tax = fields.Float(string="Sale Tax %")
    gross_amount = fields.Monetary(string='Gross Amount',
                                   store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    memo = fields.Char(string='Memo')
    available_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        compute='_compute_available_journal_ids',
        store=True
    )
    sale_wh_tax = fields.Float(string="Sale WH Tax %")
    income_wh_tax = fields.Float(string="Income WH Tax %")

    payment_mode = fields.Selection([
        ('simple', 'Simple Payment'),
        ('advance', 'Advance Payment')
    ], string="Type", default='simple')

    advance_payment_ids = fields.Many2many(
        'account.payment',
        string="Advance Payments",
    )

    advance_payment_total = fields.Monetary(
        string="Advance Payment Total",
        compute="_compute_advance_payment_total",
        currency_field='currency_id'
    )

    @api.depends('advance_payment_ids', 'payment_mode')
    def _compute_advance_payment_total(self):
        for rec in self:
            if rec.payment_mode == 'advance':
                rec.advance_payment_total = sum(rec.advance_payment_ids.mapped('amount'))
                rec.sudo().write({'amount': rec.advance_payment_total})
            else:
                rec.advance_payment_total = 0.0

    @api.onchange('amount', 'sale_tax', 'income_wh_tax', 'sale_wh_tax')
    def _onchange_compute_gross_amount(self):
        for rec in self:
            # # 1
            # # (100 / (1- (16/ (100 + 16 ) ) - (4/100) ))
            # gross_amount = abs((rec.amount / (1 - (rec.sale_tax / (100 + rec.sale_tax)) - (rec.income_wh_tax / 100))))

            # 2
            # 100 /( 1 - ( (15/115) * (20/100) )- (4/100) )
            gross_amount = abs((rec.amount / (1 - ((rec.sale_tax / (100 + rec.sale_tax)) * (rec.sale_wh_tax / 100)) - (
                    rec.income_wh_tax / 100))))
            # print('gross_amount = ', gross_amount)
            rec.sudo().write({'gross_amount': gross_amount})

    global_wh = fields.Boolean(string="Global WH")

    def action_compute_withholding(self):
        for rec in self:
            for line in rec.account_multi_payment_line_ids:
                if rec.global_wh:
                    line.sale_wh_tax = rec.sale_wh_tax
                    line.income_wh_tax = rec.income_wh_tax

                # Recompute based on change source
                if line.sale_wh_changed_by_percent:
                    if line.sale_wh_tax and line.to_pay_amount_tax:
                        line.sale_wh_tax_amount = round((line.sale_wh_tax / 100.0) * line.to_pay_amount_tax, 2)
                else:
                    if line.sale_wh_tax_amount and line.to_pay_amount_tax:
                        line.sale_wh_tax = round((line.sale_wh_tax_amount / line.to_pay_amount_tax) * 100, 2)

                if line.income_wh_changed_by_percent:
                    if line.income_wh_tax and line.amount:
                        line.income_wh_tax_amount = round((line.income_wh_tax / 100.0) * line.amount, 2)
                else:
                    if line.income_wh_tax_amount and line.amount:
                        line.income_wh_tax = round((line.income_wh_tax_amount / line.amount) * 100, 2)

                # Total payable
                line.total_pay_amount = round(
                    line.amount - (line.sale_wh_tax_amount + line.income_wh_tax_amount), 2
                )


    def action_delete_unselected_lines(self):
        for rec in self:
            if not rec.state == 'posted':
                lines_to_delete = rec.account_multi_payment_line_ids.filtered(lambda l: not l.selected)
                lines_to_delete.unlink()

    @api.depends('payment_type')
    def _compute_available_journal_ids(self):
        journals = self.env['account.journal'].search([])
        for pay in self:
            if pay.payment_type == 'inbound':
                pay.available_journal_ids = journals.filtered('inbound_payment_method_line_ids')
            else:
                pay.available_journal_ids = journals.filtered('outbound_payment_method_line_ids')

    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 )
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
                                                         compute='_compute_payment_method_line_fields')

    @api.depends('payment_type', 'journal_id', 'currency_id')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines(pay.payment_type)

    payment_method_id = fields.Many2one('account.payment.method.line', string='Payment Method', required=True)
    available_partner_bank_ids = fields.Many2many(
        comodel_name='res.partner.bank',
        compute='_compute_available_partner_bank_ids',
    )

    @api.depends('partner_id', 'payment_type')
    def _compute_available_partner_bank_ids(self):
        for pay in self:
            if pay.payment_type == 'inbound':
                pay.available_partner_bank_ids = pay.journal_id.bank_account_id
            else:
                pay.available_partner_bank_ids = pay.partner_id.bank_ids

    partner_bank_id = fields.Many2one('res.partner.bank')
    move_type = fields.Char(compute="_compute_move_type", store=True)
    sale_wh_tax_account = fields.Many2one('account.account', string="Sale WH Tax Account", required=True)
    income_wh_tax_account = fields.Many2one('account.account', string="Income WH Tax Account", required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted')
    ], string='Status', default='draft', tracking=True)

    account_multi_payment_line_ids = fields.One2many(
        'account.multi.payment.line', 'multi_payment_id', string="Invoices"
    )
    is_reversed = fields.Boolean(string="Is Reversed", copy=False)

    # @api.onchange('sale_wh_tax', 'income_wh_tax')
    # def _assign_percentages(self):
    #     for line in self.account_multi_payment_line_ids:
    #         line.income_wh_tax = self.income_wh_tax
    #         line.sale_wh_tax = self.sale_wh_tax

    @api.depends('payment_type')
    def _compute_move_type(self):
        for record in self:
            if record.payment_type == 'inbound':
                record.move_type = 'out_invoice'
            else:
                record.move_type = 'in_invoice'

    def _fetch_invoices(self):
        """
        Fetches invoices related to the selected partner and updates the One2Many field.
        """
        self.ensure_one()
        if self.partner_id:
            invoice_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', self.move_type),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ]
            invoices = self.env['account.move'].search(invoice_domain)

            new_lines = []
            for invoice in invoices:
                new_lines.append((0, 0, {
                    'invoice_id': invoice.id,
                    'name': invoice.name,
                    'invoice_date': invoice.invoice_date,
                    'due_date': invoice.invoice_date_due,
                    'invoice_amount': invoice.amount_total,
                    'residual_amount': invoice.amount_residual,
                    'amount_tax': invoice.amount_tax,
                    'status_in_payment': invoice.status_in_payment,
                    'amount_untaxed': invoice.amount_untaxed,
                    'amount': invoice.amount_residual,
                    'currency_id': invoice.currency_id.id,
                }))
            return new_lines
        return []

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('account.multi.payments') or 'New'

            record = super(AccountMultiPayments, self).create(vals)
            if record.partner_id:
                record.account_multi_payment_line_ids = record._fetch_invoices()
        return record

    def write(self, vals):
        """
        Overriding write method to fetch invoices when the partner is updated.
        """
        result = super(AccountMultiPayments, self).write(vals)
        if 'partner_id' in vals:
            for record in self:
                record.account_multi_payment_line_ids = [(5, 0, 0)]
                record.account_multi_payment_line_ids = record._fetch_invoices()
        return result

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMultiPayments, self).default_get(fields_list)
        payment_type = self.env.context.get('default_payment_type')
        if payment_type:
            res['payment_type'] = payment_type

        return res

    @api.onchange('gross_amount', 'amount')
    def _assign_to_pay_amounts(self):
        remaining_amount = self.gross_amount
        last_line = None

        for line in self.account_multi_payment_line_ids:
            line.amount = 0

        for line in self.account_multi_payment_line_ids:
            if remaining_amount <= 0:
                break

            if remaining_amount >= line.residual_amount:
                line.amount = line.residual_amount
                remaining_amount -= line.residual_amount
            else:
                last_line = line
                break

        if last_line and remaining_amount > 0:
            last_line.amount = remaining_amount

    def action_confirm(self):
        PaymentRegister = self.env['account.payment.register']
        for line in self.account_multi_payment_line_ids:
            if self.payment_mode == 'advance' and self.advance_payment_ids:
                for advance in self.advance_payment_ids:
                    advance.action_draft()
                    advance.action_cancel()

                latest_date = max(self.advance_payment_ids.mapped('date'))
                self.date = latest_date

            if not line.status_in_payment == 'paid' and line.amount > 0:
                invoice = line.invoice_id
                move_lines = invoice.line_ids
                multiplier = 1 if self.payment_type == 'inbound' else -1
                print("multiplier ", multiplier)

                wizard_vals = {
                    'sale_wh_tax': line.sale_wh_tax / 100.0,
                    'income_wh_tax': line.income_wh_tax / 100.0,
                    'amount_tax': line.amount_tax,
                    'amount': line.amount,
                    'sale_wh_tax_amount': multiplier * line.sale_wh_tax_amount,
                    'income_wh_tax_amount': multiplier * line.income_wh_tax_amount,
                    'sale_wh_tax_account': self.sale_wh_tax_account.id,
                    'income_wh_tax_account': self.income_wh_tax_account.id,
                    'payment_type': self.payment_type,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.currency_id.id,
                    'payment_date': self.date,
                    'journal_id': self.journal_id.id,
                    'company_id': self.company_id.id,
                    'payment_method_line_id': self.payment_method_id.id,
                }
                print("Wizard Values:", wizard_vals)
                wizard = PaymentRegister.with_context(
                    active_model='account.move.line',
                    active_ids=move_lines.ids
                ).create(wizard_vals)
                result = wizard.action_create_payments()
                payment_id = result['res_id']
                payment = self.env['account.payment'].browse(payment_id)
                invoice.sale_tax_due = invoice.sale_tax_due - line.sale_wh_tax_amount
                line.status_in_payment = invoice.status_in_payment
                line.payment_ids = [(4, payment.id)]
                line.payment_name = payment.name
                payment.write({'multi_payment_id': self.id})
                invoice.multi_payment_ids = [(4, payment.multi_payment_id.id)]

        if self.access_payment > 0:
            payment_vals = {
                'amount': self.access_payment,
                'payment_type': self.payment_type,
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'date': datetime.now(),
                'journal_id': self.journal_id.id,
                'company_id': self.company_id.id,
                'payment_method_line_id': self.payment_method_id.id,
            }
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()

        new_state = 'posted'
        self.write({'state': new_state})
        return True

    # def action_reverse(self):
    #     """
    #     Reverse a payment by duplicating an existing inbound payment,
    #     reversing its move entries (swapping debit and credit),
    #     and then reconciling it with the invoice.
    #     """
    #     for rec in self:
    #         if rec.state != 'posted':
    #             raise ValidationError("Only posted multipayments can be reversed.")
    #
    #         print("Processing multipayment ID:", rec.id)
    #
    #         for line in rec.account_multi_payment_line_ids.filtered(
    #                 lambda l: l.payment_ids and l.invoice_id and l.invoice_id.state == 'posted'
    #         ):
    #             invoice = line.invoice_id
    #             print("Invoice found:", invoice.name)
    #             receivable_account = invoice.partner_id.property_account_receivable_id
    #             print("Receivable account ID:", receivable_account.id)
    #
    #             # -----------------------------------------------------------------
    #             # Step 1: Unreconcile the invoice’s receivable move lines.
    #             # -----------------------------------------------------------------
    #             receivable_lines = invoice.line_ids.filtered(
    #                 lambda l: l.account_id == receivable_account and l.reconciled
    #             )
    #
    #             print("Found {} reconciled receivable lines on invoice.".format(len(receivable_lines)))
    #             if not receivable_lines:
    #                 print("No receivable lines to unreconcile for invoice", invoice.name)
    #                 continue
    #             for move_line in receivable_lines:
    #                 print("Unreconciling invoice move line ID {}: debit {}, credit {}"
    #                       .format(move_line.id, move_line.debit, move_line.credit))
    #                 move_line.remove_move_reconcile()
    #
    #             # -----------------------------------------------------------------
    #             # Step 2: Duplicate the original inbound payment.
    #             # -----------------------------------------------------------------
    #             original_payment = line.payment_ids[0]
    #             print("Original payment found:", original_payment.name)
    #             reversed_payment = original_payment.copy()
    #             reversed_payment.move_id = original_payment.move_id
    #             print("Copied reversed payment:", reversed_payment.name)
    #
    #             # -----------------------------------------------------------------
    #             # Step 3: Cancel and reset the copied payment so its move can be regenerated.
    #             # -----------------------------------------------------------------
    #             # try:
    #             #     reversed_payment.action_draft()  # Reset the payment to draft so move lines are re-created.
    #             #     print("Reversed payment reset to draft.")
    #             # except Exception as e:
    #             #     print("Error cancelling or resetting reversed payment:", e)
    #             #     raise ValidationError("Unable to cancel/reset the copied payment.")
    #
    #             # -----------------------------------------------------------------
    #             # Step 4: Reverse the journal entries in the copied payment's move.
    #             # -----------------------------------------------------------------
    #             # After calling action_post(), the payment move will be created.
    #             try:
    #                 reversed_payment.action_draft()
    #                 reversed_payment.action_post()
    #                 print("Reversed payment re-posted:", reversed_payment.name)
    #             except Exception as e:
    #                 print("Error posting reversed payment:", e)
    #                 raise ValidationError("Unable to post the reversed payment.")
    #
    #             # Now, the reversed payment should have its move
    #             # if not reversed_payment.move_id:
    #             # raise ValidationError("The reversed payment does not have an associated move after posting.")
    #             payment_move = reversed_payment.move_id
    #             print("Payment move for orignal payment:", original_payment.move_id.name)
    #             print("Payment move for reversed payment:", payment_move.name)
    #             print("lines", len(payment_move.line_ids))
    #             print("orignal lines", len(original_payment.move_id.line_ids))
    #             for move_line in original_payment.move_id.line_ids:
    #                 print(move_line.name)
    #             for move_line in payment_move.line_ids:
    #                 print(move_line.name)
    #
    #
    #             for move_line in payment_move.line_ids:
    #                 orig_debit = move_line.debit
    #                 orig_credit = move_line.credit
    #                 print("Before reversal - Move line ID {}: debit {}, credit {}"
    #                       .format(move_line.id, orig_debit, orig_credit))
    #                 # Swap debit and credit amounts.
    #                 new_debit = orig_credit
    #                 new_credit = orig_debit
    #                 orig_amt_currency = move_line.amount_currency or 0.0
    #                 new_amt_currency = -orig_amt_currency
    #                 move_line.write({
    #                     'debit': new_debit,
    #                     'credit': new_credit,
    #                     'amount_currency': new_amt_currency,
    #                 })
    #                 print("After reversal - Move line ID {}: debit {}, credit {}, amount_currency {}"
    #                       .format(move_line.id, move_line.debit, move_line.credit, move_line.amount_currency))
    #
    #             # -----------------------------------------------------------------
    #             # Step 5: Reconcile the reversed payment move lines with the invoice.
    #             # -----------------------------------------------------------------
    #             reversed_lines = payment_move.line_ids.filtered(lambda l: l.account_id == receivable_account)
    #             print("Reversed payment has {} move lines on receivable account.".format(len(reversed_lines)))
    #             # for line_rec in reversed_lines:
    #             #     print("Unreconciling reversed move line ID {} before reconciliation.".format(line_rec.id))
    #             # line_rec.remove_move_reconcile()
    #             (receivable_lines + reversed_lines).reconcile()
    #             print("Reconciliation complete for invoice", invoice.name)
    #
    #     return True

    def action_reverse(self):
        self.ensure_one()
        rec = self
        if rec.state != 'posted':
            raise ValidationError("Only Posted Multi Payments can be Reversed.")
        lines = rec.account_multi_payment_line_ids.filtered(
            lambda l: l.payment_ids and l.invoice_id and l.invoice_id.state == 'posted'
        )
        payment_ids = lines.mapped('payment_ids')
        # print('payment_ids = ', payment_ids)

        for payment_id in payment_ids:
            reversal_dict = {
                'date': fields.Date.today(),
                'journal_id': payment_id.journal_id.id,
            }
            move_reversal = self.env['account.move.reversal'].with_context(
                active_model="account.move",
                active_ids=payment_id.move_id.ids).sudo().create(reversal_dict)
            # print(f'move_reversal of payment {payment_id.name} = ', move_reversal)
            reversal = move_reversal.reverse_moves()
            # print(f'reversal of payment {payment_id.name} = ', reversal)

            reverse_payment_id = reversal.get('res_id')
            # if not reverse_payment_id:
            #     raise ValidationError("Could not create the reverse payment. Please check your configuration.")
            if reverse_payment_id:
                reverse_payment = self.env['account.move'].sudo().browse(reverse_payment_id)
                if reverse_payment:
                    # reverse_payment.sudo().action_draft()
                    reverse_payment.multi_payment_ids += rec
                    reverse_payment.ref = f'{reverse_payment.ref} from Multi Payment [ {rec.name} ]'
                    # reverse_payment.sudo().write({
                    #     "multi_payment_ids": [rec.id],
                    # })
                    # reverse_payment.sudo().action_post()

            rec.sudo().write({
                "is_reversed": True,
            })

    def action_reverse_base(self):
        """Reverses a payment by:
          1. Removing the reconciliation for the invoice’s receivable move lines,
          2. Creating a reverse outbound payment with destination_account_id forced to the invoice’s receivable account,
          3. Re-reconciling the invoice with the new reverse payment.
        """
        for rec in self:
            if rec.state != 'posted':
                raise ValidationError("Only posted multipayments can be reversed.")

            for line in rec.account_multi_payment_line_ids.filtered(
                    lambda l: l.payment_ids and l.invoice_id and l.invoice_id.state == 'posted'
            ):
                invoice = line.invoice_id
                print(invoice.move_type)
                print(invoice.name)
                # Determine the receivable account from the invoice's partner.
                receivable_account = invoice.partner_id.property_account_receivable_id

                # 1. Remove the reconciliation.
                # Filter the invoice's move lines so only those on the receivable account are considered.
                receivable_lines = invoice.line_ids.filtered(
                    lambda l: l.account_id == receivable_account and l.reconciled
                )
                if not receivable_lines:
                    continue  # Nothing to unreconcile – perhaps already reversed.
                for move_line in receivable_lines:
                    move_line.remove_move_reconcile()

                # 2. Create an outbound (send type) reverse payment.
                PaymentRegister = self.env['account.payment.register']
                wizard_vals = {
                    'sale_wh_tax': line.sale_wh_tax / 100.0,
                    'income_wh_tax': line.income_wh_tax / 100.0,
                    'amount': line.amount,
                    'partner_id': rec.partner_id.id,
                    'currency_id': rec.currency_id.id,
                    'payment_date': fields.Date.context_today(self),
                    'sale_wh_tax_amount': line.sale_wh_tax_amount,
                    'income_wh_tax_amount': line.income_wh_tax_amount,
                    'sale_wh_tax_account': rec.sale_wh_tax_account.id,
                    'income_wh_tax_account': rec.income_wh_tax_account.id,
                    'journal_id': rec.journal_id.id,
                }
                wizard = PaymentRegister.with_context(
                    active_model='account.move.line',
                    active_ids=invoice.line_ids.ids,
                ).create(wizard_vals)
                result = wizard.action_create_payments()

                reverse_payment_id = result.get('res_id')
                if not reverse_payment_id:
                    raise ValidationError("Could not create the reverse payment. Please check your configuration.")
                reverse_payment = self.env['account.payment'].browse(reverse_payment_id)
                print("reversed payment", reverse_payment.name)
                print("reversed payment", reverse_payment.payment_type)
                print("reversed payment", len(reverse_payment.move_id.line_ids))
                for move_line in reverse_payment.move_id.line_ids:
                    print(move_line.name)

                for move_line in reverse_payment.move_id.line_ids:
                    move_line.remove_move_reconcile()
                    orig_debit = move_line.debit
                    orig_credit = move_line.credit
                    print("Before reversal - Move line ID {}: debit {}, credit {}"
                          .format(move_line.id, orig_debit, orig_credit))
                    # Swap debit and credit amounts.
                    new_debit = orig_credit
                    new_credit = orig_debit
                    orig_amt_currency = move_line.amount_currency or 0.0
                    new_amt_currency = -orig_amt_currency
                    move_line.write({
                        'debit': new_debit,
                        'credit': new_credit,
                        'amount_currency': new_amt_currency,
                    })
                    print("After reversal - Move line ID {}: debit {}, credit {}, amount_currency {}"
                          .format(move_line.id, move_line.debit, move_line.credit, move_line.amount_currency))

                # 3. Reconcile the newly created reverse payment with the invoice.
                # Get only the move lines posted on the receivable account.
                reverse_move_lines = reverse_payment.move_id.line_ids.filtered(
                    lambda l: l.account_id == receivable_account
                )
                for move_line in reverse_move_lines:
                    move_line.remove_move_reconcile()
                (receivable_lines + reverse_move_lines).reconcile()
        return True

    def action_view_payments(self):
        self.ensure_one()
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.payment',
            'domain': [('multi_payment_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_view_invoices(self):
        self.ensure_one()
        invoice_ids = self.account_multi_payment_line_ids.mapped('invoice_id').ids
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'create': False},
        }

    def action_cancel(self):
        self.state = 'draft'

    def action_reset_to_draft(self):
        self.state = 'draft'

    total_invoice_amount = fields.Monetary(string="Total Invoice Amount", compute="_compute_totals", store=True)
    total_residual_amount = fields.Monetary(string="Total Due Amount", compute="_compute_totals", store=True)
    total_tax_amount = fields.Monetary(string="Total Tax Amount", compute="_compute_totals", store=True)
    total_untaxed_amount = fields.Monetary(string="Total Untaxed Amount", compute="_compute_totals", store=True)
    total_to_pay = fields.Monetary(string="Total To Pay", compute="_compute_totals", store=True)
    total_sale_wh_tax = fields.Monetary(string="Total Sale WH Tax Amount", compute="_compute_totals", store=True)
    total_income_wh_tax = fields.Monetary(string="Total Income WH Tax Amount", compute="_compute_totals", store=True)
    total_pay_amount = fields.Monetary(string="Total Pay Amount", compute="_compute_totals", store=True)
    access_payment = fields.Monetary(string="Excess Payment", compute="_compute_totals", store=True)

    @api.depends('account_multi_payment_line_ids.selected',
                 'account_multi_payment_line_ids.invoice_amount',
                 'account_multi_payment_line_ids.residual_amount',
                 'account_multi_payment_line_ids.amount_tax',
                 'account_multi_payment_line_ids.amount_untaxed',
                 'account_multi_payment_line_ids.amount',
                 'account_multi_payment_line_ids.sale_wh_tax_amount',
                 'account_multi_payment_line_ids.income_wh_tax_amount',
                 'account_multi_payment_line_ids.total_pay_amount')
    def _compute_totals(self):
        """Compute rounded totals from only the selected lines."""
        for record in self:
            selected_lines = record.account_multi_payment_line_ids.filtered(lambda l: l.selected)

            record.total_invoice_amount = round(sum(selected_lines.mapped('invoice_amount')), 2)
            record.total_residual_amount = round(sum(selected_lines.mapped('residual_amount')), 2)
            record.total_tax_amount = round(sum(selected_lines.mapped('amount_tax')), 2)
            record.total_untaxed_amount = round(sum(selected_lines.mapped('amount_untaxed')), 2)
            record.total_to_pay = round(sum(selected_lines.mapped('amount')), 2)
            record.total_sale_wh_tax = round(sum(selected_lines.mapped('sale_wh_tax_amount')), 2)
            record.total_income_wh_tax = round(sum(selected_lines.mapped('income_wh_tax_amount')), 2)
            record.total_pay_amount = round(sum(selected_lines.mapped('total_pay_amount')), 2)
            record.access_payment = round(record.amount - record.total_pay_amount, 2)
