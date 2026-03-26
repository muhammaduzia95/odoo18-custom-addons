# -*- coding: utf-8 -*-
# from odoo import http


# class VisioInheritResContact(http.Controller):
#     @http.route('/visio_inherit_res_contact/visio_inherit_res_contact', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/visio_inherit_res_contact/visio_inherit_res_contact/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('visio_inherit_res_contact.listing', {
#             'root': '/visio_inherit_res_contact/visio_inherit_res_contact',
#             'objects': http.request.env['visio_inherit_res_contact.visio_inherit_res_contact'].search([]),
#         })

#     @http.route('/visio_inherit_res_contact/visio_inherit_res_contact/objects/<model("visio_inherit_res_contact.visio_inherit_res_contact"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('visio_inherit_res_contact.object', {
#             'object': obj
#         })

