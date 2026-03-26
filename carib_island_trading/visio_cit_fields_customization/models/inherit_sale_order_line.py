# visio_cit_fields_customization/models/sale_order_line.py
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    default_code = fields.Char(related='product_id.default_code', store=True, readonly=True)
    barcode = fields.Char(related='product_id.barcode', store=True, readonly=True)
    categ_id = fields.Many2one(related='product_id.categ_id', comodel_name='product.category', store=True,
                               readonly=True)
    size = fields.Char(related="product_id.size", store=True, readonly=True, )
    # per_unit_price = fields.Float(string="Pcs Price", compute="_compute_per_unit_price", store=True)

    # @api.depends('price_unit', 'product_id.cit_case_qty')
    # def _compute_per_unit_price(self):
    #     for line in self:
    #         case_qty = line.product_id.cit_case_qty or 0
    #         if line.price_unit and case_qty > 0:
    #             line.per_unit_price = line.price_unit / case_qty
    #         else:
    #             line.per_unit_price = 0.0

    per_unit_price = fields.Float(
        string="Pcs Price",
        compute="_compute_per_unit_price",
        inverse="_inverse_per_unit_price",
        store=True,
        readonly=False,
    )

    @api.depends("price_unit", "product_id.product_tmpl_id.cit_case_qty")
    def _compute_per_unit_price(self):
        for line in self:
            case_qty = float(line.product_id.product_tmpl_id.cit_case_qty or 0.0)
            line.per_unit_price = (line.price_unit / case_qty) if (case_qty and line.price_unit) else 0.0

    def _inverse_per_unit_price(self):
        """When user edits pcs price -> update Odoo price_unit (case price).
        We DO NOT touch technical_price_unit so Odoo treats it as a manual price and won't recompute it.
        """
        for line in self:
            case_qty = float(line.product_id.product_tmpl_id.cit_case_qty or 0.0)
            line.price_unit = (line.per_unit_price * case_qty) if case_qty else 0.0

    @api.onchange("per_unit_price")
    def _onchange_per_unit_price(self):
        for line in self:
            case_qty = float(line.product_id.product_tmpl_id.cit_case_qty or 0.0)
            if case_qty:
                line.price_unit = (line.per_unit_price or 0.0) * case_qty

    # -----------

    per_unit = fields.Many2one(
        'uom.uom', string="Per Unit", compute='_compute_per_unit', store=True, readonly=True)

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

    # units_quantity = fields.Float(string="Pcs Order", compute="_compute_units_quantity", store=True)
    #
    # @api.depends('product_uom_qty', 'product_id.cit_case_qty')
    # def _compute_units_quantity(self):
    #     for line in self:
    #         case_qty = line.product_id.cit_case_qty or 0
    #         line.units_quantity = line.product_uom_qty * case_qty

    region_cit = fields.Char(string="Region")
    hs_code_cit = fields.Char(string="H.S Code")
    translated_product_name = fields.Char(string="Translated Product Name", invisible="1")
    vendor_price_cit = fields.Float(string='Vendor Unit Price (PR)',
                                    help='Temporary unit price used only by the Purchase Request workflow.')

    vendor_subtotal_cit = fields.Monetary(
        string="Vendor Subtotal",
        compute="_compute_vendor_subtotal_cit",
        currency_field="currency_id",
    )

    @api.depends("product_uom_qty", "vendor_price_cit")
    def _compute_vendor_subtotal_cit(self):
        for line in self:
            line.vendor_subtotal_cit = (line.product_uom_qty or 0.0) * (line.vendor_price_cit or 0.0)

    # Sync the Region, HS Code fields with the sale order
    def _prepare_invoice_line(self, **optional_values):
        vals = super()._prepare_invoice_line(**optional_values)

        vals.update({
            'region_cit_inv': self.region_cit,
            'hs_code_cit_inv': self.hs_code_cit,
            'units_quantity': self.units_quantity,
            'quantity': self.product_uom_qty,
        })
        print("Vals:", vals)
        return vals

    # Editable field (NO compute)
    # units_quantity = fields.Float(string="Pcs Order", default=0.0)
    #
    # def _cit_case_factor(self):
    #     """How many pcs in 1 case."""
    #     self.ensure_one()
    #     return float(self.product_id.cit_case_qty or 0.0)
    #
    # # CASE -> PCS
    # @api.onchange("product_uom_qty", "product_id")
    # def _onchange_case_to_pcs(self):
    #     for line in self:
    #         if line.env.context.get("cit_skip_case_to_pcs"):
    #             continue
    #
    #         factor = line._cit_case_factor()
    #         line.units_quantity = line.product_uom_qty * factor if factor else 0.0
    #
    # # PCS -> CASE
    # @api.onchange("units_quantity", "product_id")
    # def _onchange_pcs_to_case(self):
    #     for line in self:
    #         if line.env.context.get("cit_skip_pcs_to_case"):
    #             continue
    #
    #         factor = line._cit_case_factor()
    #         # avoid loop
    #         line_ctx = line.with_context(cit_skip_case_to_pcs=True)
    #         line_ctx.product_uom_qty = (line.units_quantity / factor) if factor else 0.0
    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #     lines = super().create(vals_list)
    #     lines._cit_sync_after_save()
    #     return lines
    #
    # def write(self, vals):
    #     res = super().write(vals)
    #     if not self.env.context.get("cit_skip_server_sync"):
    #         self.with_context(cit_skip_server_sync=True)._cit_sync_after_save()
    #     return res
    #
    # def _cit_sync_after_save(self):
    #     """Server-side sync (imports/RPC) so fields stay consistent."""
    #     for line in self:
    #         factor = line._cit_case_factor()
    #         if not factor:
    #             continue
    #
    #         # If user wrote units_quantity -> update product_uom_qty
    #         # Else -> update units_quantity from product_uom_qty
    #         # (deterministic rule)
    #         if self.env.context.get("cit_prefer_units") or False:
    #             line.with_context(cit_skip_server_sync=True).sudo().write({
    #                 "product_uom_qty": line.units_quantity / factor
    #             })
    #         else:
    #             line.with_context(cit_skip_server_sync=True).sudo().write({
    #                 "units_quantity": line.product_uom_qty * factor
    #             })

    units_quantity = fields.Float(
        string="Pcs Order",
        compute="_compute_units_quantity",
        inverse="_inverse_units_quantity",
        store=True,
    )

    @api.depends("product_uom_qty", "product_id.cit_case_qty")
    def _compute_units_quantity(self):
        for line in self:
            factor = float(line.product_id.cit_case_qty or 0.0)  # pcs per case
            line.units_quantity = line.product_uom_qty * factor if factor else 0.0

    def _inverse_units_quantity(self):
        for line in self:
            factor = float(line.product_id.cit_case_qty or 0.0)  # pcs per case
            line.product_uom_qty = (line.units_quantity / factor) if factor else 0.0

    # # updating the value of CS Price
    # @api.depends("per_unit_price", "product_id.product_tmpl_id.cit_case_qty")
    # def _compute_price_unit(self):
    #     print("def _compute_price_unit")
    #     for line in self:
    #         print("line", line)
    #         case_qty = line.product_id.product_tmpl_id.cit_case_qty or 0
    #         line.price_unit = (line.per_unit_price or 0.0) * case_qty
    #         print("case_qty >>>>", case_qty)
    #         print("(line.per_unit_price >>>>", line.per_unit_price)
