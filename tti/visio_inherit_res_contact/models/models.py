# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class visio_inherit_res_contact(models.Model):
#     _name = 'visio_inherit_res_contact.visio_inherit_res_contact'
#     _description = 'visio_inherit_res_contact.visio_inherit_res_contact'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

