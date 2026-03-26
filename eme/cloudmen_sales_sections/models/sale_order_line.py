from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    note_subtotal = fields.Float(string='Note Subtotal', compute="get_note_subtotal")
    category_subtotal = fields.Float(string='Category Subtotal', compute="get_category_total")
    category_total_qty = fields.Float(string='Category Total Qty', compute="get_category_total")

    product_brand_origin = fields.Char(string='Brand / Origin', readonly=False, store=False,
                                       compute="_compute_product_brand_origin")

    def _compute_product_brand_origin(self):
        for line in self:
            barcode = line.product_id.barcode or ''
            default_code = line.product_id.default_code or ''
            line.product_brand_origin = f"{barcode} {default_code}".strip()



    @api.depends('order_id.order_line')
    def get_category_total(self):
        for line in self:
            if line.display_type == 'line_section':
                category_subtotal = 0.0
                category_total_qty = 0.0
                sale_order = line.order_id
                lines = sale_order.order_line.sorted('sequence')
                line_ids = lines.ids
                base_line_index = line_ids.index(line.id)

                # Calculate totals for lines after the current section line
                for subsequent_line in lines[base_line_index + 1:]:
                    if subsequent_line.display_type == 'line_section':
                        break
                    else:
                        category_subtotal += subsequent_line.price_subtotal
                        category_total_qty += subsequent_line.product_uom_qty

                # Assign the calculated values
                line.category_subtotal = category_subtotal
                line.category_total_qty = category_total_qty
            else:
                line.category_subtotal = 0.0
                line.category_total_qty = 0.0

    def get_note_subtotal(self):
        for base_line in self:
            if base_line.display_type == 'line_note':
                line_subtotal = 0.0
                sale_order = base_line.order_id
                lines = sale_order.order_line.sorted('sequence')
                line_ids = lines.ids
                base_line_index = line_ids.index(base_line.id)
                for line in lines[base_line_index + 1:]:
                    if line.display_type in ('line_note', 'line_section'):
                        break
                    else:
                        line_subtotal += line.price_subtotal
                base_line.note_subtotal = line_subtotal
            else:
                base_line.note_subtotal = 0.0
