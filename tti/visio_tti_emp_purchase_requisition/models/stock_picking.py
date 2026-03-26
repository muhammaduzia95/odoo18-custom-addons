# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import ValidationError

class Picking(models.Model):
    """Class to add new field in stock picking"""

    _inherit = 'stock.picking'

    requisition_order = fields.Char(
        string='Requisition Order',
        help='Requisition order sequence')


class StockMove(models.Model):
    """Class to add new field in stock picking"""

    _inherit = 'stock.move'

    def write(self, vals):
        res = super().write(vals)
        for move in self:
            if move.picking_id.picking_type_id.code in ['incoming', 'internal'] and move.picking_id.picking_type_id.sequence_code in ['IGP', 'GIN', 'GRN']:
                if move.product_uom_qty < move.quantity:
                    raise ValidationError("You can't transfer more than the Initial Demand!")
        return res
