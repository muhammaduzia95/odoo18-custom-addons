# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class mail_composer_cc_bcc(models.Model):
#     _name = 'mail_composer_cc_bcc.mail_composer_cc_bcc'
#     _description = 'mail_composer_cc_bcc.mail_composer_cc_bcc'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

