# -*- coding: utf-8 -*-
# from odoo import http


# class VisioTtiDashboard(http.Controller):
#     @http.route('/visio_tti_dashboard/visio_tti_dashboard', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/visio_tti_dashboard/visio_tti_dashboard/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('visio_tti_dashboard.listing', {
#             'root': '/visio_tti_dashboard/visio_tti_dashboard',
#             'objects': http.request.env['visio_tti_dashboard.visio_tti_dashboard'].search([]),
#         })

#     @http.route('/visio_tti_dashboard/visio_tti_dashboard/objects/<model("visio_tti_dashboard.visio_tti_dashboard"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('visio_tti_dashboard.object', {
#             'object': obj
#         })

