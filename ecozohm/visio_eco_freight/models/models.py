# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class visio_eco_freight(models.Model):
#     _name = 'visio_eco_freight.visio_eco_freight'
#     _description = 'visio_eco_freight.visio_eco_freight'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

