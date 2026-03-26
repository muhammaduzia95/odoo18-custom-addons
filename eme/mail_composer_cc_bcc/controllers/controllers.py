# -*- coding: utf-8 -*-
# from odoo import http


# class MailComposerCcBcc(http.Controller):
#     @http.route('/mail_composer_cc_bcc/mail_composer_cc_bcc', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mail_composer_cc_bcc/mail_composer_cc_bcc/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mail_composer_cc_bcc.listing', {
#             'root': '/mail_composer_cc_bcc/mail_composer_cc_bcc',
#             'objects': http.request.env['mail_composer_cc_bcc.mail_composer_cc_bcc'].search([]),
#         })

#     @http.route('/mail_composer_cc_bcc/mail_composer_cc_bcc/objects/<model("mail_composer_cc_bcc.mail_composer_cc_bcc"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mail_composer_cc_bcc.object', {
#             'object': obj
#         })

