# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.fields import Command
from odoo.exceptions import ValidationError


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    has_order_lines = fields.Boolean(compute='_compute_has_order_lines')
    section_id = fields.Many2one('sale.order.line', string='Section',
                                 domain="[('display_type', '=', 'line_section'), ('order_id', '=', id)]" )
    # , ('has_products', '=', True)

    @api.depends('order_line')
    def _compute_has_order_lines(self):
        for order in self:
            if len(order.order_line) > 0:
                order.has_order_lines = len(order.order_line)
            else:
                order.has_order_lines = 0

    def copy_order_lines(self):
        self.section_id = None
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale_renting.rental_order_action")
        action.update({
            'name': _('Confirm'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [
                (self.env.ref('copy_order_line.copy_order_line_form_view').id, 'form')],
            'res_model': 'sale.order',
            'target': 'new',
            'res_id': self.id,

        })
        return action

    # def confirm_copy_lines(self):
    #     global related_section
    #     if not self.section_id:
    #         raise ValidationError(_('Please select section!'))
    #     if len(self.order_line) > 0 and self.section_id:
    #         section_products = self.order_line.filtered(lambda x: x.section_id == self.section_id)
    #         all_lines_for_copy = self.section_id + section_products
    #         # Find the maximum sequence number among existing lines
    #         max_sequence = max(self.order_line.mapped('sequence'), default=0)
    #         # Append new lines with sequence numbers greater than the max_sequence
    #         for line in all_lines_for_copy:
    #             if line.display_type == 'line_section':
    #                 related_section = line.id
    #             self.write({
    #                 'order_line': [(0, 0, {
    #                     'name': line.name,
    #                     'product_id': line.product_id.id,
    #                     'product_uom_qty': line.product_uom_qty,
    #                     'price_unit': line.price_unit,
    #                     'product_uom': line.product_uom.id,
    #                     'product_packaging_id': line.product_packaging_id.id,
    #                     'display_type': line.display_type,
    #                     'tax_id': [(6, 0, line.tax_id.ids)],
    #                     'sequence': max_sequence + 1,  # Set the sequence number higher than the max
    #                     'discount': line.discount,
    #                     'price_subtotal': line.price_subtotal,
    #                     # 'section_id': len(self.order_line) + 1 if line.display_type != 'line_section' else False
    #                 })]
    #             })
    #             max_sequence += 1  # Increment the max_sequence for the next line
    @api.model
    def copy_section_with_products(self,order_id,line_id):
        order = self.env['sale.order'].browse(order_id)

        if len(order.order_line) > 0 and line_id:
            section_selected = order.order_line.filtered(lambda x: x.id == line_id)
            start_index = order.order_line.ids.index(section_selected.id) + 1
            # Find the maximum sequence number among existing lines
            max_sequence = max(order.order_line.mapped('sequence'), default=0)


            order.write({
                'order_line': [(0, 0, {
                    'name': section_selected.name + ' (copied)',
                    'product_id': section_selected.product_id.id,
                    'product_uom_qty': section_selected.product_uom_qty,
                    'price_unit': section_selected.price_unit,
                    'product_uom': section_selected.product_uom.id,
                    'product_packaging_id': section_selected.product_packaging_id.id,
                    'display_type': section_selected.display_type,
                    'tax_id': [(6, 0, section_selected.tax_id.ids)],
                    'sequence': max_sequence + 1,  # Set the sequence number higher than the max
                    'discount': section_selected.discount,
                    'price_subtotal': section_selected.price_subtotal,
                    # 'section_id': len(self.order_line) + 1 if line.display_type != 'line_section' else False
                })]
            })
            max_sequence += 1  # Increment the max_sequence for the next line
            for line in order.order_line[start_index:]:
                if line.display_type == 'line_section':
                   break
                order.write({
                    'order_line': [(0, 0, {
                        'name': line.name ,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'product_uom': line.product_uom.id,
                        'product_packaging_id': line.product_packaging_id.id,
                        'display_type': line.display_type,
                        'tax_id': [(6, 0, line.tax_id.ids)],
                        'sequence': max_sequence + 1,  # Set the sequence number higher than the max
                        'discount': line.discount,
                        'price_subtotal': line.price_subtotal,
                        # 'section_id': len(self.order_line) + 1 if line.display_type != 'line_section' else False
                    })]
                })
                max_sequence += 1  # Increment the max_sequence for the next line
            return order

    def confirm_copy_lines(self):
        if not self.section_id:
            raise ValidationError(_('Please select section!'))
        if len(self.order_line) > 0 and self.section_id:
            section_selected = self.order_line.filtered(lambda x: x.id == self.section_id.id)
            start_index = self.order_line.ids.index(section_selected.id) + 1
            # Find the maximum sequence number among existing lines
            max_sequence = max(self.order_line.mapped('sequence'), default=0)


            self.write({
                'order_line': [(0, 0, {
                    'name': section_selected.name + ' (copied)',
                    'product_id': section_selected.product_id.id,
                    'product_uom_qty': section_selected.product_uom_qty,
                    'price_unit': section_selected.price_unit,
                    'product_uom': section_selected.product_uom.id,
                    'product_packaging_id': section_selected.product_packaging_id.id,
                    'display_type': section_selected.display_type,
                    'tax_id': [(6, 0, section_selected.tax_id.ids)],
                    'sequence': max_sequence + 1,  # Set the sequence number higher than the max
                    'discount': section_selected.discount,
                    'price_subtotal': section_selected.price_subtotal,
                    # 'section_id': len(self.order_line) + 1 if line.display_type != 'line_section' else False
                })]
            })
            max_sequence += 1  # Increment the max_sequence for the next line
            for line in self.order_line[start_index:]:
                if line.display_type == 'line_section':
                   break
                self.write({
                    'order_line': [(0, 0, {
                        'name': line.name ,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'product_uom': line.product_uom.id,
                        'product_packaging_id': line.product_packaging_id.id,
                        'display_type': line.display_type,
                        'tax_id': [(6, 0, line.tax_id.ids)],
                        'sequence': max_sequence + 1,  # Set the sequence number higher than the max
                        'discount': line.discount,
                        'price_subtotal': line.price_subtotal,
                        # 'section_id': len(self.order_line) + 1 if line.display_type != 'line_section' else False
                    })]
                })
                max_sequence += 1  # Increment the max_sequence for the next line



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # section_id = fields.Many2one('sale.order.line', string='Section', )
    # has_products = fields.Boolean(compute='_compute_has_products',default=False,store=True)
    #
    # @api.depends('section_id','order_id.order_line')
    # def _compute_has_products(self):
    #     for rec in self:
    #         section_products = rec.order_id.order_line.mapped('section_id')
    #         if rec.id in list(set(section_products.ids)):
    #             rec.has_products = True
    #         else:
    #             rec.has_products = False

    @api.depends('order_partner_id', 'order_id', 'product_id', 'name')
    def _compute_display_name(self):
        # name_per_id = self._additional_name_per_id()
        for so_line in self.sudo():
            # name = '{} - {}'.format(so_line.order_id.name,
            #                         so_line.name and so_line.name.split('\n')[0] or so_line.product_id.name)
            # additional_name = name_per_id.get(so_line.id)
            # if additional_name:
            #     name = f'{name} {additional_name}'
            so_line.display_name = so_line.name
