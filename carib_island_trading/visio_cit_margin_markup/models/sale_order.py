# D:\Visiomate\Odoo\odoo18\custom_addons\carib_island_trading\visio_cit_margin_markup\models\sale_order.py
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    markup_percent = fields.Integer(string="Markup (%)", help="Enter the markup percentage to apply on this order.")
    margin_percent = fields.Integer(string="Margin (%)", help="Enter the margin percentage to apply on this order.")

    @api.onchange('markup_percent', 'margin_percent')
    def _onchange_percent_propagate(self):
        for order in self:
            for line in order.order_line:
                line.markup_percent_line = order.markup_percent
                line.margin_percent_line = order.margin_percent


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    markup_percent_line = fields.Integer(string="Markup (%)", help="Line-level markup (defaults from order header).")
    margin_percent_line = fields.Integer(string="Margin (%)", help="Line-level margin (defaults from order header).")

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'markup_percent_line', 'margin_percent_line', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit or 0.0
            qty = line.product_uom_qty or 0.0
            disc_pct = line.discount or 0.0
            markup_pct = line.markup_percent_line or 0.0
            margin_pct = line.margin_percent_line or 0.0

            if margin_pct:
                denom = 100.0 - margin_pct
                if denom <= 0:
                    subtotal = 0.0
                else:
                    base_unit = price * 100.0 / denom
                    net_unit = base_unit * (1.0 - disc_pct / 100.0)
                    subtotal = net_unit * qty
            elif markup_pct:
                base_unit = price * (1.0 + markup_pct / 100.0)
                net_unit = base_unit * (1.0 - disc_pct / 100.0)
                subtotal = net_unit * qty
            else:
                # fallback to Odoo default when no markup/margin
                super(SaleOrderLine, line)._compute_amount()
                continue

            line.update({
                'price_subtotal': subtotal,
                'price_total': subtotal,  # assuming no taxes
                'price_tax': 0.0,
            })

    @api.model
    def create(self, vals):
        if vals.get('order_id'):
            order = self.env['sale.order'].browse(vals['order_id'])
            if not vals.get('markup_percent_line'):
                vals['markup_percent_line'] = order.markup_percent or 0
            if not vals.get('margin_percent_line'):
                vals['margin_percent_line'] = order.margin_percent or 0
        return super().create(vals)
