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

    # @api.depends('product_qty', 'product_id.cit_case_qty')
    # def _compute_units_quantity(self):
    #     for line in self:
    #         case_qty = line.product_id.cit_case_qty or 0
    #         line.units_quantity = line.product_qty * case_qty if case_qty > 0 else 0.0

    @api.depends('product_qty', 'product_id', 'product_id.cit_case_qty', 'product_id.product_tmpl_id.cit_case_qty')
    def _compute_units_quantity(self):
        for line in self:
            case_qty = float(
                line.product_id.product_tmpl_id.cit_case_qty
                or line.product_id.cit_case_qty
                or 0.0
            )
            line.units_quantity = line.product_qty * case_qty if case_qty > 0 else line.product_qty

    # @api.depends('price_unit', 'product_id.cit_case_qty')
    # def _compute_per_unit_price(self):
    #     for line in self:
    #         case_qty = line.product_id.cit_case_qty or 0
    #         if line.price_unit and case_qty > 0:
    #             line.price_per_unit = line.price_unit / case_qty
    #         else:
    #             line.price_per_unit = 0.0

    @api.depends('price_unit', 'product_id', 'product_id.cit_case_qty', 'product_id.product_tmpl_id.cit_case_qty')
    def _compute_per_unit_price(self):
        for line in self:
            case_qty = float(
                line.product_id.product_tmpl_id.cit_case_qty
                or line.product_id.cit_case_qty
                or 0.0
            )
            if case_qty > 0:
                line.price_per_unit = (line.price_unit or 0.0) / case_qty
            else:
                line.price_per_unit = line.price_unit or 0.0

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
        return vals

    @api.depends("move_ids.state", "move_ids.scrapped", "move_ids.cs_order_cit")
    def _compute_qty_received(self):
        # keep Odoo standard for everything else
        super()._compute_qty_received()

        # override ONLY for purchase lines that compute from receipts
        for line in self.filtered(lambda l: l.qty_received_method == "stock_moves"):
            done_moves = line.move_ids.filtered(lambda m: m.state == "done" and not m.scrapped)
            line.qty_received = sum(done_moves.mapped("cs_order_cit"))

    @api.onchange("product_id", "product_qty", "product_uom", "order_id.partner_id", "order_id.date_order")
    def _onchange_product_id_set_price_unit(self):
        print("\n=== PO _onchange_product_id_set_price_unit START ===")
        for line in self:
            print("\n--- Processing PO line ---")
            print("line id:", line.id)
            print("product_id:", line.product_id.id if line.product_id else False)
            print("vendor:", line.order_id.partner_id.id if line.order_id.partner_id else False)
            print("qty:", line.product_qty)

            if not line.product_id:
                print("No product found, setting price_unit = 0.0")
                line.price_unit = 0.0
                continue

            case_qty = float(
                line.product_id.product_tmpl_id.cit_case_qty
                or line.product_id.cit_case_qty
                or 0.0
            )
            qty = line.product_qty or 1.0

            # default fallback = standard price
            unit_price = float(line.product_id.standard_price or 0.0)

            print("case_qty:", case_qty)
            print("qty:", qty)
            print("default standard_price:", unit_price)

            seller = False
            if line.order_id.partner_id:
                seller = line.product_id._select_seller(
                    partner_id=line.order_id.partner_id,
                    quantity=qty,
                    date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.today(),
                    uom_id=line.product_uom,
                )

            print("seller found:", seller.id if seller else False)

            if seller:
                unit_price = float(seller.price or 0.0)
                print("vendor price found:", unit_price)
            else:
                print("No vendor price found, using standard_price:", unit_price)

            line.price_unit = unit_price * case_qty if case_qty > 0 else unit_price

            print("final price_unit:", line.price_unit)

        print("=== PO _onchange_product_id_set_price_unit END ===\n")
