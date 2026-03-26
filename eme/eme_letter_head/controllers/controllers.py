# -*- coding: utf-8 -*-
# from odoo import http


# class EmeLetterHead(http.Controller):
#     @http.route('/eme_letter_head/eme_letter_head', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/eme_letter_head/eme_letter_head/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('eme_letter_head.listing', {
#             'root': '/eme_letter_head/eme_letter_head',
#             'objects': http.request.env['eme_letter_head.eme_letter_head'].search([]),
#         })

#     @http.route('/eme_letter_head/eme_letter_head/objects/<model("eme_letter_head.eme_letter_head"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('eme_letter_head.object', {
#             'object': obj
#         })

