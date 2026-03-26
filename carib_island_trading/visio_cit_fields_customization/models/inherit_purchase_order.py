from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    default_code = fields.Char(related="product_id.default_code", store=True, readonly=True)
    barcode = fields.Char(related="product_id.barcode", store=True, readonly=True)
    categ_id = fields.Many2one(comodel_name="product.category", related="product_id.categ_id", store=True,
                               readonly=True)
    size = fields.Char(related="product_id.size", store=True, readonly=True)

    units_quantity = fields.Float(string="Pcs Order", compute='_compute_units_quantity', store=True)
    price_per_unit = fields.Float(string="Pcs Price", compute="_compute_per_unit_price", store=True)
    per_unit = fields.Many2one('uom.uom', string="Per Unit", compute='_compute_per_unit', store=True, readonly=True)

    @api.depends('product_qty', 'product_id.cit_case_qty')
    def _compute_units_quantity(self):
        for line in self:
            case_qty = line.product_id.cit_case_qty or 0
            line.units_quantity = line.product_qty * case_qty if case_qty > 0 else 0.0

    @api.depends('price_unit', 'product_id.cit_case_qty')
    def _compute_per_unit_price(self):
        for line in self:
            case_qty = line.product_id.cit_case_qty or 0
            if line.price_unit and case_qty > 0:
                line.price_per_unit = line.price_unit / case_qty
            else:
                line.price_per_unit = 0.0

    @api.depends('product_id')
    def _compute_per_unit(self):
        for line in self:
            if line.product_id.uom_id and line.product_id.uom_id.category_id:
                unit_uom = self.env['uom.uom'].search([
                    ('category_id', '=', line.product_id.uom_id.category_id.id),
                    ('uom_type', '=', 'reference')
                ], limit=1)
                line.per_unit = unit_uom
            else:
                line.per_unit = False

    def _prepare_account_move_line(self, move=False):
        vals = super()._prepare_account_move_line(move)
        vals.update({
            'quantity': self.product_qty,
            'units_quantity': self.units_quantity,
        })
        print("")
        print("")
        print("")
        print("")
        print("")

        print("Bill Line Vals:", vals)
        print("")
        return vals

    @api.depends("move_ids.state", "move_ids.scrapped", "move_ids.cs_order_cit")
    def _compute_qty_received(self):
        # keep Odoo standard for everything else
        super()._compute_qty_received()

        # override ONLY for purchase lines that compute from receipts
        for line in self.filtered(lambda l: l.qty_received_method == "stock_moves"):
            done_moves = line.move_ids.filtered(lambda m: m.state == "done" and not m.scrapped)
            line.qty_received = sum(done_moves.mapped("cs_order_cit"))
