# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class eme_letter_head(models.Model):
#     _name = 'eme_letter_head.eme_letter_head'
#     _description = 'eme_letter_head.eme_letter_head'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

