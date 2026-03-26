# -*- coding: utf-8 -*-
# carib_island_trading\visio_cit_purchase_request\models\purchase_request.py
from odoo import fields, models, api


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _order = 'id desc'   # newest first
    _rec_name = 'sale_order_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True, readonly=True, tracking=True)
    vendor_ids = fields.Many2one('res.partner', string="Vendors", tracking=True, domain="[('supplier_rank', '>', 0)]")
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate')], default='draft', string='Status',
                             tracking=True)

    def action_validate(self):
        for rec in self:
            # Create PO
            po = self.env['purchase.order'].create({
                'partner_id': rec.vendor_ids.id,
                'origin': rec.sale_order_id.name,
                'order_line': [],
                'notes': rec.note_pr,
            })

            for so_line in rec.sale_order_id.order_line:
                self.env['purchase.order.line'].create({
                    'order_id': po.id,
                    'product_id': so_line.product_id.id,
                    'name': so_line.name,
                    'product_qty': so_line.product_uom_qty,
                    'product_uom': so_line.product_uom.id,
                    # 'price_unit': so_line.price_unit,
                    'price_unit': so_line.vendor_price_cit,
                    'date_planned': fields.Date.today(),
                })

            rec.state = 'validate'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Validated!",
                'message': f"Purchase Order {po.name} has been created and validated.",
                'next': {'type': 'ir.actions.act_window_close'},
                'type': 'success',
                'sticky': False,
            }
        }

    # order_line_ids = fields.One2many(related="sale_order_id.order_line", string="Sale Order Lines",
    # readonly=True, help="All lines from the linked Sale Order", )

    filtered_so_line_ids = fields.One2many(
        comodel_name='sale.order.line',
        compute='_compute_filtered_order_lines',
        string='Filtered Sale Order Lines',
        readonly=True,
    )

    # Removing the down payment form purchase request view
    @api.depends('sale_order_id')
    def _compute_filtered_order_lines(self):
        for rec in self:
            rec.filtered_so_line_ids = (
                rec.sale_order_id.order_line.filtered(lambda l: not l.is_downpayment)
                if rec.sale_order_id else
                self.env['sale.order.line']
            )

            print("rec", rec)
            print("rec.sale_order_id", rec.sale_order_id)
            print("rec.filtered_so_line_ids ", rec.filtered_so_line_ids)

    # changing the price on purchase request, price is coming from the vendor
    # in purchase_request.py
    @api.onchange('vendor_ids')
    def _onchange_vendor_ids(self):
        """Pull the vendor’s price into each non-down-payment SOL."""
        if not self.vendor_ids or not self.sale_order_id:
            return

        supplierinfo = self.env['product.supplierinfo']
        vendor = self.vendor_ids

        for line in self.sale_order_id.order_line.filtered(lambda l: not l.is_downpayment):
            sinfo = supplierinfo.search([
                ('partner_id', '=', vendor.id),
                '|',
                ('product_id', '=', line.product_id.id),
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
            ], order='min_qty asc, sequence asc', limit=1)

            line.vendor_price_cit = sinfo.price if sinfo else 0.0

        print("sinfo", sinfo)
        print("sinfo.price", sinfo.price)

    note_pr = fields.Html(string="Terms and Conditions")
