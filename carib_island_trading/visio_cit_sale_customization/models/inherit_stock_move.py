# carib_island_trading\visio_cit_sale_customization\models\inherit_stock_move.py
from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    barcode = fields.Char(string="UPC")
    size = fields.Char(string="Size")
    region_cit = fields.Char(string="Region")
    hs_code_cit = fields.Char(string="H.S Code")
    cs_order_cit = fields.Float(string="CS Order")

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            values = {}
            line = move.sale_line_id or move.purchase_line_id
            if line:
                values.update({
                    'barcode': getattr(line, 'barcode', False),
                    'size': getattr(line, 'size', False),
                    'region_cit': getattr(line, 'region_cit', False),
                    'hs_code_cit': getattr(line, 'hs_code_cit', False),
                    # SO line uses product_uom_qty; PO line uses product_qty
                    'cs_order_cit': getattr(line, 'product_uom_qty', getattr(line, 'product_qty', 0.0)),
                })
                # if you store units on the line, copy them
                if hasattr(line, 'units_quantity'):
                    values['product_uom_qty'] = line.units_quantity

            if values:
                move.write(values)
        return moves

    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     if vals.get('sale_line_id'):
    #         sale_line = self.env['sale.order.line'].browse(vals['sale_line_id'])
    #         res.barcode = sale_line.barcode
    #         res.size = sale_line.size
    #         res.region_cit = sale_line.region_cit
    #         res.hs_code_cit = sale_line.hs_code_cit
    #         res.cs_order_cit = sale_line.product_uom_qty
    #         res.product_uom_qty = sale_line.units_quantity
    #     return res
