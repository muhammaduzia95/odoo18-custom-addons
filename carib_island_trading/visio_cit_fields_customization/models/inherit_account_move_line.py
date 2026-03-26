from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    print("[DEBUG] Loading AccountMoveLine model")

    default_code = fields.Char(related="product_id.default_code", store=True, readonly=True)
    barcode = fields.Char(related="product_id.barcode", store=True, readonly=True)
    categ_id = fields.Many2one(comodel_name="product.category", related="product_id.categ_id", store=True,
                               readonly=True)
    size = fields.Char(related="product_id.size", store=True, readonly=True)
    # units_quantity = fields.Float(string="Pcs Order", compute='_compute_units_quantity', store=True)
    units_quantity = fields.Float(string="Pcs Order", store=True)
    price_per_unit = fields.Float(string="Pcs Price", compute="_compute_per_unit_price", store=True)
    per_unit = fields.Many2one('uom.uom', string="Per Unit", compute='_compute_per_unit', store=True, readonly=True)

    print("[DEBUG] Fields defined for AccountMoveLine")

    # @api.depends('quantity', 'product_id.cit_case_qty')
    # def _compute_units_quantity(self):
    #     for line in self:
    #         case_qty = line.product_id.cit_case_qty or 0
    #         line.units_quantity = line.quantity * case_qty if case_qty > 0 else 0.0
    #         print(f"[DEBUG _compute_units_quantity] Line ID: {line.id}, Quantity: {line.quantity}, "
    #               f"Case Qty: {case_qty}, Units Quantity: {line.units_quantity}")

    @api.depends('price_unit', 'product_id.cit_case_qty')
    def _compute_per_unit_price(self):
        print("[DEBUG] Entering _compute_per_unit_price")
        for line in self:
            print(f"[DEBUG] Processing line ID: {line.id}")
            case_qty = line.product_id.cit_case_qty or 0
            print(f"[DEBUG] case_qty: {case_qty}")

            if line.price_unit and case_qty > 0:
                print("[DEBUG] Condition met: price_unit and case_qty > 0")
                line.price_per_unit = line.price_unit / case_qty
            else:
                print("[DEBUG] Condition NOT met, setting 0.0")
                line.price_per_unit = 0.0

            print(f"[DEBUG _compute_per_unit_price] Line ID: {line.id}, Price Unit: {line.price_unit}, "
                  f"Case Qty: {case_qty}, Price per Unit: {line.price_per_unit}")

    @api.depends('product_id')
    def _compute_per_unit(self):
        print("[DEBUG] Entering _compute_per_unit")
        for line in self:
            print(f"[DEBUG] Processing line ID: {line.id}")

            if line.product_id.uom_id and line.product_id.uom_id.category_id:
                print("[DEBUG] Product has UoM and category")

                unit_uom = self.env['uom.uom'].search([
                    ('category_id', '=', line.product_id.uom_id.category_id.id),
                    ('uom_type', '=', 'reference')
                ], limit=1)

                print(f"[DEBUG] Found unit_uom: {unit_uom}")

                line.per_unit = unit_uom

                print(f"[DEBUG _compute_per_unit] Line ID: {line.id}, Product: {line.product_id.display_name}, "
                      f"Unit UoM: {unit_uom.display_name}")
            else:
                print("[DEBUG] Product missing UoM or category")

                line.per_unit = False

                print(
                    f"[DEBUG _compute_per_unit] Line ID: {line.id}, Product: {line.product_id.display_name if line.product_id else 'N/A'}, "
                    f"Unit UoM: None")

    region_cit_inv = fields.Char(string='Region')
    hs_code_cit_inv = fields.Char(string='H.S Code')

    print("[DEBUG] AccountMoveLine model fully loaded")

    def _prepare_product_base_line_for_taxes_computation(self, product_line):
        base_line = super()._prepare_product_base_line_for_taxes_computation(product_line)

        sale_line = product_line.sale_line_ids[:1]
        if sale_line and (sale_line.markup_percent_line or sale_line.margin_percent_line):
            base_line['price_unit'] = sale_line._cit_effective_unit_before_discount()

        return base_line

