# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    x_studio_material_required_date = fields.Date(string='Material Required Date')

# class cloudmen_approval_print(models.Model):
#     _name = 'cloudmen_approval_print.cloudmen_approval_print'
#     _description = 'cloudmen_approval_print.cloudmen_approval_print'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

