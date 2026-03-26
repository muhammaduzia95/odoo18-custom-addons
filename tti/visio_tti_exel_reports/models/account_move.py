from odoo import models , fields , api

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

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    tti_si_category_ids = fields.Many2many(
        'tti.si.category',
        string="Category",
        compute='_compute_tti_si_category_ids',
        store=True
    )

    @api.depends('reconciled_invoice_ids', 'reconciled_invoice_ids.tti_si_category_ids')
    def _compute_tti_si_category_ids(self):
        for payment in self:
            invoices = payment.reconciled_invoice_ids
            payment.tti_si_category_ids = [(6, 0, invoices.mapped('tti_si_category_ids').ids)]


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tti_report_type = fields.Selection(
        related='account_id.tti_report_type',
        string='TTI Report Type',
        store=True,
        readonly=True
    )