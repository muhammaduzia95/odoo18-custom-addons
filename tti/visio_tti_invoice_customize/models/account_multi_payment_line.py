from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMultiPaymentLine(models.Model):
    _name = 'account.multi.payment.line'
    _description = 'Multi Payment Line'

    name = fields.Char(string='Name', )
    multi_payment_id = fields.Many2one('account.multi.payments', string="Multi Payment")
    invoice_id = fields.Many2one('account.move', string="Invoice", required=True, readonly=True)
    invoice_date = fields.Date(string="Invoice Date", readonly=True)
    due_date = fields.Date(string="Due Date", readonly=True)
    invoice_amount = fields.Monetary(string="Invoice Amount", readonly=True)
    residual_amount = fields.Monetary(string="Due Amount", readonly=True)
    currency_id = fields.Many2one('res.currency')
    to_pay_amount_tax = fields.Monetary(string="To Pay Tax", store=True, compute="_compute_to_pay_amount_tax")
    amount_tax = fields.Monetary(string="Tax", store=True)
    amount_untaxed = fields.Monetary(string="Untaxed Amount", store=True)
    amount = fields.Monetary(string="To Pay", store=True)
    total_pay_amount = fields.Monetary(string="Total Pay Amount", compute="compute_total_pay_amount", store=True)
    status_in_payment = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('in_payment', 'In Payment')
    ])
    payment_ids = fields.Many2many(
        'account.payment',
        string="Payments"
    )
    payment_name = fields.Char(string="Payment Ref")

    sale_wh_tax = fields.Float(string="Sale WH Tax %", store=True)
    income_wh_tax = fields.Float(string="Income WH Tax %", default=0.0, store=True)

    sale_wh_tax_amount = fields.Monetary(
        # compute="_compute_tax_amount",
        store=True
    )
    income_wh_tax_amount = fields.Monetary(
        # compute="_compute_tax_amount",
        store=True
    )
    selected = fields.Boolean(string="Select")
    sale_wh_changed_by_percent = fields.Boolean(string="Sale WH Changed by %", default=True)
    income_wh_changed_by_percent = fields.Boolean(string="Income WH Changed by %", default=True)

    @api.depends('multi_payment_id.sale_tax', 'amount')
    def _compute_to_pay_amount_tax(self):
        for move in self:
            tax_rate = move.multi_payment_id.sale_tax or 0.0
            if tax_rate > 0:
                untaxed_amount = move.amount / (1 + tax_rate / 100)
                move.to_pay_amount_tax = move.amount - untaxed_amount
            else:
                move.to_pay_amount_tax = 0.0

    # @api.onchange('amount', 'income_wh_tax')
    # def recompute_income_wh_tax(self):
    #     for record in self:
    #         income_wh_tax_amount = round((record.income_wh_tax / 100.0) * record.amount, 2)
    #         record.sudo().write({'income_wh_tax_amount': income_wh_tax_amount})

    def write(self, vals):
        if 'sale_wh_tax' in vals:
            vals['sale_wh_changed_by_percent'] = True
        elif 'sale_wh_tax_amount' in vals:
            vals['sale_wh_changed_by_percent'] = False

        if 'income_wh_tax' in vals:
            vals['income_wh_changed_by_percent'] = True
        elif 'income_wh_tax_amount' in vals:
            vals['income_wh_changed_by_percent'] = False

        res = super().write(vals)
        return res


    @api.depends('amount', 'sale_wh_tax_amount', 'income_wh_tax_amount')
    def compute_total_pay_amount(self):
        for record in self:
            total = record.amount - (record.sale_wh_tax_amount + record.income_wh_tax_amount)
            record.total_pay_amount = round(total, 2)


# @api.depends('sale_wh_tax', 'income_wh_tax', 'amount', 'amount_tax', 'sale_wh_tax_amount', 'income_wh_tax_amount')
# def _compute_tax_amount(self):
#     """Compute tax amounts based on percentage and total amount."""
#     for record in self:
#         record.sale_wh_tax_amount = (record.sale_wh_tax / 100) * record.amount_tax
#         record.income_wh_tax_amount = (record.income_wh_tax / 100) * record.amount
#
# @api.onchange('sale_wh_tax', 'income_wh_tax', 'amount', 'amount_tax', 'sale_wh_tax_amount', 'income_wh_tax_amount')
# def _onchange_tax_fields(self):
#     """Trigger real-time update when tax percentage or amount changes."""
#     for record in self:
#         record.sale_wh_tax_amount = (record.sale_wh_tax / 100) * record.amount_tax
#         record.income_wh_tax_amount = (record.income_wh_tax  / 100) * record.amount

    @api.constrains('sale_wh_tax', 'income_wh_tax')
    def _check_tax_percentage(self):
        """Ensure the tax percentage is between 0 and 100"""
        for record in self:
            if record.sale_wh_tax < 0:
                raise ValidationError("Sale WH Tax % must be positive.")
            if record.income_wh_tax < 0:
                raise ValidationError("Income WH Tax % must be positive.")
