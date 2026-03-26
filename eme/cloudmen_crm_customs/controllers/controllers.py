# -*- coding: utf-8 -*-
# from odoo import http


# class CloudmenCrmCustoms(http.Controller):
#     @http.route('/cloudmen_crm_customs/cloudmen_crm_customs', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cloudmen_crm_customs/cloudmen_crm_customs/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cloudmen_crm_customs.listing', {
#             'root': '/cloudmen_crm_customs/cloudmen_crm_customs',
#             'objects': http.request.env['cloudmen_crm_customs.cloudmen_crm_customs'].search([]),
#         })

#     @http.route('/cloudmen_crm_customs/cloudmen_crm_customs/objects/<model("cloudmen_crm_customs.cloudmen_crm_customs"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cloudmen_crm_customs.object', {
#             'object': obj
#         })

