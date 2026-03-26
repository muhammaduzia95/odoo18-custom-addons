from odoo import models, fields, api , _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    partner_category_ids = fields.Many2many('res.partner.category', related='partner_id.category_id', readonly=True)

# class AccountJournal(models.Model):
#     _inherit = "account.journal"
#
#     def _get_default_account_domain(self):
#         return """[
#             ('deprecated', '=', False),
#             ('account_type', 'in', ('asset_cash', 'liability_credit_card', 'asset_current') if type == 'bank'
#                                    else ('liability_credit_card',) if type == 'credit'
#                                    else ('asset_cash',) if type == 'cash'
#                                    else ('income', 'income_other') if type == 'sale'
#                                    else ('expense', 'expense_depreciation', 'expense_direct_cost') if type == 'purchase'
#                                    else ('asset_receivable', 'asset_cash', 'asset_current', 'asset_non_current',
#                                          'asset_prepayments', 'asset_fixed', 'liability_payable',
#                                          'liability_credit_card', 'liability_current', 'liability_non_current',
#                                          'equity', 'equity_unaffected', 'income', 'income_other', 'expense',
#                                          'expense_depreciation', 'expense_direct_cost', 'off_balance'))
#         ]"""


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_order_ids = fields.Many2many(
        'sale.order',
        string='Related Sale Orders',
        compute='_compute_sale_order_ids',
        store=True
    )

    tti_si_category_ids = fields.Many2many(
        'tti.si.category',
        string="Category",
        compute='_compute_sale_order_info',
        store=True
    )

    tti_si_sub_category_ids = fields.Many2many(
        'tti.si.sub.category',
        string="Sub Category",
        compute='_compute_sale_order_info',
        store=True
    )

    city_zone = fields.Many2one(
        'tti.city.zone',
        string="Partner City Zone",
        compute='_compute_city_zone',
        store=True
    )
    state = fields.Selection(
        selection_add=[
            ('make', 'Make'),
            ('check', 'Check'),
        ],
        ondelete={
            'make': 'set default',
            'check': 'set default',
        },
    )

    def action_make(self):
        for move in self:
            move.state = 'make'
            if not move.name and move.move_type == 'entry':
                move.name = 'Draft'
            if move.move_type == 'out_invoice':
                move.name = 'Draft'

    def action_check(self):
        for move in self:
            move.state = 'check'
            if not move.name and move.move_type == 'entry':
                move.name = 'Draft'
            if move.move_type == 'out_invoice':
                move.name = 'Draft'

    @api.depends('partner_id')
    def _compute_city_zone(self):
        for move in self:
            move.city_zone = move.partner_id.tti_city_zone_id.id if move.partner_id.tti_city_zone_id else False


    @api.depends('line_ids', 'line_ids.sale_line_ids')
    def _compute_sale_order_ids(self):
        for invoice in self:
            invoice.sale_order_ids = invoice.line_ids.mapped('sale_line_ids.order_id')

    @api.depends('partner_id',
                 'sale_order_ids.tti_si_category',
                 'sale_order_ids.tti_si_sub_category')
    def _compute_sale_order_info(self):
        for move in self:
            sale_orders = move.sale_order_ids
            move.tti_si_category_ids = [(6, 0, sale_orders.mapped('tti_si_category').ids)]
            move.tti_si_sub_category_ids = [(6, 0, sale_orders.mapped('tti_si_sub_category').ids)]

    def _get_last_sequence_domain(self, relaxed=False):
        where_clause, params = super()._get_last_sequence_domain(relaxed)

        excluded_prefixes = ('P-', 'S-', 'K-', 'I-','C-','Draft')
        for idx, prefix in enumerate(excluded_prefixes):
            where_clause += f" AND {self._sequence_field} NOT LIKE %(custom_prefix_{idx})s"
            params[f'custom_prefix_{idx}'] = f'{prefix}%'

        return where_clause, params

    # def action_post(self):
        # for move in self:
        #     if not move.name and move.move_type == 'out_invoice':
        #         month_year = datetime.now().strftime('%m%y')
        #         state_code = move.partner_id.state_id.code if move.partner_id.state_id else ''
        #         company = move.company_id

        #         # 1. Check for reusable sequence
        #         reuse_seq = self.env['reusable.invoice.sequence'].search([
        #             ('state_code', '=', state_code),
        #             ('company_id', '=', company.id)
        #         ], limit=1)

        #         if reuse_seq:
        #             move.name = f'{reuse_seq.sequence_value}-{month_year}'
        #             reuse_seq.unlink()  # remove it from reusable pool
        #         else:
        #             # 2. Use next sequence
        #             seq_code_map = {
        #                 'PB': 'invoice.punjab',
        #                 'SD': 'invoice.sindh',
        #                 'KP': 'invoice.kpk',
        #                 'KPK': 'invoice.kpk',
        #                 'IT': 'invoice.international',
        #             }
        #             seq_code = seq_code_map.get(state_code)
        #             if seq_code:
        #                 seq = self.env['ir.sequence'].with_company(company).next_by_code(seq_code) or '00000'
        #                 move.name = f'{seq}-{month_year}'

        # return super().action_post()


    def action_post(self):
        for move in self:
            if move.name == 'Draft' and move.move_type == 'out_invoice':
                move.name = False
            if not move.name and move.move_type == 'out_invoice':
                invoice_date = move.invoice_date or fields.Date.context_today(move)
                month_year = invoice_date.strftime('%m%y')

                state_code = move.partner_id.state_id.code or ''
                company = move.company_id

                _logger.info("Processing Invoice ID %s", move.id)
                _logger.info("Invoice Date: %s", invoice_date)
                _logger.info("Month-Year: %s", month_year)
                _logger.info("State Code: %s", state_code)
                _logger.info("Company: %s", company.name)

                # 1. Check for reusable sequence
                reuse_seq = self.env['reusable.invoice.sequence'].sudo().search([
                    ('state_code', '=', state_code),
                    ('month_year', '=', month_year),
                    ('company_id', '=', company.id)
                ], limit=1)

                if reuse_seq:
                    move.name = f'{reuse_seq.sequence_value}-{month_year}'
                    _logger.info("Using reusable sequence: %s", move.name)
                    reuse_seq.sudo().unlink()
                    _logger.info("Reusable sequence unlinked: %s", reuse_seq.id)
                else:
                    # 2. Use monthly sequence with auto date range
                    seq_code_map = {
                        'PB': 'invoice.punjab',
                        'SD': 'invoice.sindh',
                        'KP': 'invoice.kpk',
                        'KPK': 'invoice.kpk',
                        'IT': 'invoice.international',
                    }
                    seq_code = seq_code_map.get(state_code)
                    _logger.info("Sequence Code: %s", seq_code)

                    if seq_code:
                        sequence = self.env['ir.sequence'].with_company(company).sudo().search([
                            ('code', '=', seq_code),
                        ], limit=1)
                        _logger.info("Found Sequence ID: %s", sequence.id if sequence else 'None')


                        if sequence and not sequence.use_date_range:
                            sequence.use_date_range = True
                            _logger.info("Enabled date range on sequence ID: %s", sequence.id)

                        if sequence and sequence.use_date_range:
                            # Compute date range for the invoice's month
                            date_from = invoice_date.replace(day=1)
                            date_to = (date_from + relativedelta(months=1)) - relativedelta(days=1)
                            _logger.info("Date Range From: %s, To: %s", date_from, date_to)

                            # Check or create the date range record
                            date_range = self.env['ir.sequence.date_range'].sudo().search([
                                ('sequence_id', '=', sequence.id),
                                ('date_from', '=', date_from),
                                ('date_to', '=', date_to),
                            ], limit=1)
                            _logger.info("sequence date range: %s", date_range.id)


                            if not date_range:
                                date_range = self.env['ir.sequence.date_range'].sudo().create({
                                    'sequence_id': sequence.id,
                                    'date_from': date_from,
                                    'date_to': date_to,
                                    'number_next': 1,
                                })
                                _logger.info("Created new sequence date range: %s", date_range.id)


                            # Manually fetch and increment the number from this date range
                            number = str(date_range.number_next_actual or 1).zfill(sequence.padding or 5)
                            _logger.info("Generated Sequence Number: %s", number)

                            # date_range.number_next_actual += 1
                            number_next_actual = date_range.number_next_actual + 1
                            date_range.sudo().write({
                                'number_next_actual':  number_next_actual
                            })

                            move.name = f'{sequence.prefix}{number}-{month_year}'
                            _logger.info("Assigned Invoice Name: %s", move.name)
                        else:
                            # Fallback to normal sequence without date range
                            seq = self.env['ir.sequence'].with_company(company).next_by_code(seq_code) or '00000'
                            move.name = f'{seq}-{month_year}'
                            _logger.info("Used fallback sequence: %s", move.name)

        return super().action_post()


    def button_cancel(self):
        for move in self:
            if move.name and move.move_type == 'out_invoice':
                # Extract reusable part: e.g., P-00015-0525 -> P-00015
                base_name = '-'.join(move.name.split('-')[:2])
                state_code = move.partner_id.state_id.code if move.partner_id.state_id else ''
                company = move.company_id

                invoice_date = move.invoice_date or fields.Date.context_today(move)
                month_year = invoice_date.strftime('%m%y')

                # ✅ Add it to reusable sequence pool
                self.env['reusable.invoice.sequence'].create({
                    'state_code': state_code,
                    'month_year': month_year,
                    'sequence_value': base_name,
                    'company_id': company.id
                })

                # ✅ Assign a new cancellation sequence name
                cancel_seq = self.env['ir.sequence'].with_company(company).next_by_code(
                    'invoice.cancelled') or 'C-00000'
                move.name = cancel_seq

        return super().button_cancel()

    def unlink(self):
        for move in self:
            if move.state == 'cancel':  # assuming 'cancel' is the cancel state in your model
                raise ValidationError(_("You cannot delete a cancelled invoice."))
        return super(AccountMove, self).unlink()

    multi_payment_ids = fields.Many2many('account.multi.payments', string="Multi Payment", copy=False)

    def action_view_multi_payments(self):
        self.ensure_one()
        return {
            'name': 'Multi Payments',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.multi.payments',
            'domain': [('id', 'in', self.multi_payment_ids.ids)],
            'context': {'create': False},
        }

    sale_tax_due = fields.Monetary(
        string="Sale Tax Due",
        compute="_compute_sale_tax_due",
        store=True
    )

    #
    # untaxed_amount_due = fields.Monetary(
    #     string="Untaxed Amount Due",
    #     compute="_compute_untaxed_amount_due",
    #     store=True
    # )
    #
    # @api.depends('amount_residual')
    # def _compute_untaxed_amount_due(self):
    #     for move in self:
    #         tax_ids = move.invoice_line_ids.
    #         untaxed_amount_due = move.amount_residual - ()

    @api.depends('amount_tax')
    def _compute_sale_tax_due(self):
        for record in self:
            record.sale_tax_due = record.amount_tax

    tti_dollar_exchange_rate = fields.Float(
        compute='_compute_current_tti_dollar_exchange_rate',
        string="Dollar Exchange Rate",
        digits=0,
        readonly=True,
        store=True,
        help='Dollar Exchange Rate'
    )

    @api.depends('currency_id', 'invoice_date')
    def _compute_current_tti_dollar_exchange_rate(self):
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

        for move in self:
            if move.currency_id and usd_currency:
                rate = usd_currency._get_conversion_rate(usd_currency, move.currency_id, move.company_id,
                                                         move.invoice_date or fields.Date.today())
                print("rate is ", rate)
                move.tti_dollar_exchange_rate = rate
            else:
                move.tti_dollar_exchange_rate = 0.0

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        if 'journal_id' in vals:
            for move in self:
                if move.move_type in ['out_invoice', 'out_refund']:
                    new_journal = self.env['account.journal'].browse(vals['journal_id'])
                    new_account = new_journal.default_account_id
                    if new_account:
                        for line in move.invoice_line_ids:
                            line.account_id = new_account
        return res


# @api.onchange('partner_id', 'invoice_line_ids')
# def _onchange_partner_id_apply_taxes(self):
#     """Apply purchase_taxes from res.partner to all invoice lines when partner_id is changed."""
#     for move in self:
#         if move.partner_id and move.move_type == 'out_invoice':
#             for line in move.invoice_line_ids:
#                 line.tax_ids = [(6, 0, (line.tax_ids.ids + move.partner_id.sales_taxes.ids))]
#         elif move.partner_id and move.move_type == 'in_invoice':
#             for line in move.invoice_line_ids:
#                 line.tax_ids = [(6, 0, (line.tax_ids.ids + move.partner_id.purchase_taxes.ids))]


class AccountGroup(models.Model):
    _inherit = 'account.group'

    analytic_required = fields.Boolean("Requires Analytic")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_vendor_bill = fields.Boolean(
        string="Is Bill Line",
        compute='_compute_is_vendor_bill',
        store=True
    )

    @api.depends('move_id.move_type')
    def _compute_is_vendor_bill(self):
        for line in self:
            line.is_vendor_bill = line.move_id.move_type in ['in_invoice', 'in_refund']

    price_unit_rate = fields.Float(string="Dollar Rate", compute='_compute_price_unit_rate', readonly=True, store=True)
    dollar_exchange_rate = fields.Float(string="Dollar Exchange Rate", related='move_id.tti_dollar_exchange_rate',
                                        readonly=True, store=True)


    @api.depends('price_unit', 'dollar_exchange_rate')
    def _compute_price_unit_rate(self):
        for record in self:
            record.price_unit_rate = record.price_unit / record.dollar_exchange_rate if record.dollar_exchange_rate else 0.0

    @api.model_create_multi
    def create(self, values):
        res = super(AccountMoveLine, self).create(values)
        res._check_analytic_field()
        return res

    def write(self, values):
        res = super(AccountMoveLine, self).write(values)
        self._check_analytic_field()
        return res

    def _check_analytic_field(self):
        # Check if the 'analytic' field is set
        account_move_lines = self.filtered(lambda x: x.move_id and x.move_id.move_type == 'entry')
        for line in account_move_lines:
            if not line.analytic_distribution:
                # Get the account group related to the account_id
                account_group = line.account_id.group_id
                # If the group has the 'analytic_required' flag and the analytic field is empty
                if account_group and account_group.analytic_required:
                    raise ValidationError(
                        f"Please select an analytic account for the selected [{line.account_id.display_name}] account in the journal entry line."
                    )
