# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    """Class to add new field in purchase order"""

    _inherit = 'purchase.order'

    requisition_order = fields.Char(
        string='Requisition Order', copy=False,
        help='Set a requisition Order')

    def button_unlock(self):
        order_lines = self.order_line.mapped('qty_received')
        sum_qty_received = sum(order_lines)
        if sum_qty_received != 0:
            raise ValidationError(f'If any Purchase Order line quantity has been received, then no changes can be made to the Purchase Order afterward!')
        res = super().button_unlock()
        return res

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            if order.partner_id:
                if not order.partner_id.street:
                    raise ValidationError(f'Please, Add Vendor Address info!')
                if not order.partner_id.vat:
                    raise ValidationError(f'Please, Add Vendor NTN Number!')
        return res

    @api.model_create_multi
    def create(self, list_vals):
        res = super().create(list_vals)
        for vals in list_vals:
            requisition_order = vals.get('requisition_order')
            print('requisition_order = ', requisition_order)
            # if not requisition_order:
            #     raise ValidationError(f'PO Creation only from Purchase Requisition Form!')
        return res

