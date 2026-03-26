# -*- coding: utf-8 -*-
# from odoo import http


# class CloudmenSalesSections(http.Controller):
#     @http.route('/cloudmen_sales_sections/cloudmen_sales_sections', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cloudmen_sales_sections/cloudmen_sales_sections/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cloudmen_sales_sections.listing', {
#             'root': '/cloudmen_sales_sections/cloudmen_sales_sections',
#             'objects': http.request.env['cloudmen_sales_sections.cloudmen_sales_sections'].search([]),
#         })

#     @http.route('/cloudmen_sales_sections/cloudmen_sales_sections/objects/<model("cloudmen_sales_sections.cloudmen_sales_sections"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cloudmen_sales_sections.object', {
#             'object': obj
#         })

