# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class visio_cit_reports(models.Model):
#     _name = 'visio_cit_reports.visio_cit_reports'
#     _description = 'visio_cit_reports.visio_cit_reports'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

