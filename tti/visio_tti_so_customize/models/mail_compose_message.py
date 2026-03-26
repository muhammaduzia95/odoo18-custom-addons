from odoo import models, api
import base64
import logging

_logger = logging.getLogger(__name__)


class CustomMailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.depends('composition_mode', 'model', 'res_domain', 'res_ids', 'template_id')
    def _compute_attachment_ids(self):
        for composer in self:
            res_ids = composer._evaluate_res_ids() or [0]

            # Call base method first
            super(CustomMailComposeMessage, composer)._compute_attachment_ids()

            if composer.model != 'sale.order' or len(res_ids) != 1:
                continue

            sale_order = self.env['sale.order'].browse(res_ids[0])
            print("sale order", sale_order.name)

            try:
                if any(
                        email.emails_to_receive in ['quotation', 'all']
                        for email in sale_order.sale_email_ids
                ):
                    pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                        'visio_tti_so_invoice_report.action_custom_sale_report',
                        res_ids=[sale_order.id]
                    )

                    attachment = self.env['ir.attachment'].create({
                        'name': 'TTI_Quotation.pdf',
                        'type': 'binary',
                        'datas': base64.b64encode(pdf_content),
                        'res_model': 'sale.order',
                        'res_id': sale_order.id,
                        'mimetype': 'application/pdf',
                    })
                    print("attachmen", attachment.id)

                    # Append to composer attachments
                    composer.attachment_ids = [(6, 0, [attachment.id])]

            except Exception as e:
                _logger.exception("Failed to generate or attach custom Sale Order PDF: %s", e)

    @api.depends('composition_mode', 'model', 'parent_id', 'res_domain',
                 'res_ids', 'template_id')
    def _compute_partner_ids(self):
        for composer in self:
            if composer.model == 'sale.order':
                res_ids = composer._evaluate_res_ids() or []
                sale_order = composer.env['sale.order'].browse(res_ids[0])
                partner_ids = []

                for email_line in sale_order.sale_email_ids:
                    if email_line.emails_to_receive in ['quotation', 'all'] and email_line.email:
                        partner = composer.env['res.partner'].search([('email', '=', email_line.email)], limit=1)
                        if not partner:
                            partner = composer.env['res.partner'].create({
                                'name': email_line.email,
                                'email': email_line.email,
                            })
                        partner_ids.append(partner.id)

                if partner_ids:
                    composer.partner_ids = [(6, 0, partner_ids)]
                else:
                    composer.partner_ids = False


class AccountMoveSendWizard(models.TransientModel):
    _inherit = 'account.move.send.wizard'

    @api.depends('mail_template_id', 'mail_lang')
    def _compute_mail_subject_body_partners(self):
        super()._compute_mail_subject_body_partners()

        for wizard in self:
            move = wizard.move_id
            sale_order = move.invoice_origin and self.env['sale.order'].search([('name', '=', move.invoice_origin)],
                                                                               limit=1)
            print("sale order", sale_order.name)

            if sale_order and sale_order.sale_email_ids:
                # Filter emails that should receive quotation or all
                filtered_emails = sale_order.sale_email_ids.filtered(
                    lambda e: e.emails_to_receive in ['invoice', 'all']
                )

                partner_ids = []
                for email_rec in filtered_emails:
                    email = email_rec.email.strip()
                    if email:
                        partner = self.env['res.partner'].search([('email', '=', email)], limit=1)
                        if not partner:
                            partner = self.env['res.partner'].create({
                                'name': email,
                                'email': email,
                            })
                        partner_ids.append(partner.id)

                if partner_ids:
                    wizard.mail_partner_ids = [(6, 0, partner_ids)]

    @api.depends('mail_template_id', 'sending_methods', 'extra_edis')
    def _compute_mail_attachments_widget(self):
        super()._compute_mail_attachments_widget()

        for wizard in self:
            move = wizard.move_id
            sale_order = move.invoice_origin and self.env['sale.order'].search([('name', '=', move.invoice_origin)],
                                                                               limit=1)

            if sale_order and sale_order.sale_email_ids:
                email_values = sale_order.sale_email_ids.mapped('emails_to_receive')
                if email_values and all(v in ['invoice', 'all'] for v in email_values):
                    try:
                        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                            'visio_tti_so_invoice_report.action_custom_invoice_from_saleorder',
                            res_ids=[move.id]
                        )

                        # Create the PDF attachment
                        attachment = self.env['ir.attachment'].create({
                            'name': 'TTI_Invoice.pdf',
                            'type': 'binary',
                            'datas': base64.b64encode(pdf_content).decode(),
                            'res_model': 'account.move',
                            'res_id': move.id,
                            'mimetype': 'application/pdf',
                        })

                        # Only include the new custom PDF
                        wizard.mail_attachments_widget = [{
                            'id': attachment.id,
                            'name': attachment.name,
                            'mimetype': attachment.mimetype,
                            'manual': True,
                        }]

                    except Exception as e:
                        _logger.exception("Failed to render or attach custom sale order PDF: %s", e)


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _get_mail_params(self, move, move_data):
        # We must ensure the newly created PDF are added. At this point, the PDF has been generated but not added
        # to 'mail_attachments_widget'.
        mail_attachments_widget = move_data.get('mail_attachments_widget')
        seen_attachment_ids = set()
        to_exclude = {x['name'] for x in mail_attachments_widget if x.get('skip')}
        for attachment_data in mail_attachments_widget:
            if attachment_data['name'] in to_exclude and not attachment_data.get('manual'):
                continue

            try:
                attachment_id = int(attachment_data['id'])
            except ValueError:
                continue

            seen_attachment_ids.add(attachment_id)

        mail_attachments = [
            (attachment.name, attachment.raw)
            for attachment in self.env['ir.attachment'].browse(list(seen_attachment_ids)).exists()
        ]

        return {
            'author_id': move_data['author_partner_id'],
            'body': move_data['mail_body'],
            'subject': move_data['mail_subject'],
            'partner_ids': move_data['mail_partner_ids'],
            'attachments': mail_attachments,
        }