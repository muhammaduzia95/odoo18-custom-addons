# -*- coding: utf-8 -*-
# from odoo import http


# class VisioEcoFreight(http.Controller):
#     @http.route('/visio_eco_freight/visio_eco_freight', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/visio_eco_freight/visio_eco_freight/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('visio_eco_freight.listing', {
#             'root': '/visio_eco_freight/visio_eco_freight',
#             'objects': http.request.env['visio_eco_freight.visio_eco_freight'].search([]),
#         })

#     @http.route('/visio_eco_freight/visio_eco_freight/objects/<model("visio_eco_freight.visio_eco_freight"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('visio_eco_freight.object', {
#             'object': obj
#         })

