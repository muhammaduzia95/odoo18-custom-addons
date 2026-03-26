# -*- coding: utf-8 -*-
# from odoo import http


# class FieldsIsOdoo(http.Controller):
#     @http.route('/fields_is_odoo/fields_is_odoo', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fields_is_odoo/fields_is_odoo/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fields_is_odoo.listing', {
#             'root': '/fields_is_odoo/fields_is_odoo',
#             'objects': http.request.env['fields_is_odoo.fields_is_odoo'].search([]),
#         })

#     @http.route('/fields_is_odoo/fields_is_odoo/objects/<model("fields_is_odoo.fields_is_odoo"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fields_is_odoo.object', {
#             'object': obj
#         })

