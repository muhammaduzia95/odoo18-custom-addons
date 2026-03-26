# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_report_sending\models\inherit_sale_order.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import re
import html


class SaleOrder(models.Model):
    _inherit = "sale.order"

    can_send_report = fields.Boolean(string="Can Send Report", compute="_compute_can_send_report")
    report_sent = fields.Boolean(string="Report Sent", default=False)
    report_link_main = fields.Char(string="Primary Report Link", copy=False)

    def _ensure_report_link_main(self):
        """Extract the first href, unescape it properly, and force-save the clean URL."""
        import html
        for order in self:
            html_src = order.report_urls_html or ""
            print(f"[REPORT LINK] scanning SO {order.name} (id={order.id}) | html_len={len(html_src)}")

            m = re.search(r'href\s*=\s*([\'"])(.*?)\1', html_src, flags=re.IGNORECASE | re.DOTALL)
            if not m:
                print("[REPORT LINK] href not found in report_urls_html")
                continue

            raw = m.group(2)
            clean = html.unescape(raw).replace("&amp;", "&")  # 🔥 ensure all &amp; are gone
            order.report_link_main = clean

            print(f"[REPORT LINK] RAW   -> {raw}")
            print(f"[REPORT LINK] CLEAN -> {clean}")

    @api.depends('invoice_ids.state')
    def _compute_can_send_report(self):
        for order in self:
            user = self.env.user
            has_posted_invoice = bool(order.invoice_ids.filtered(lambda inv: inv.state == 'posted'))
            if user.has_group('visio_tti_report_sending.group_sale_order_send_report_manager'):
                order.can_send_report = True
            elif user.has_group('visio_tti_report_sending.group_sale_order_send_report_user'):
                order.can_send_report = has_posted_invoice
            else:
                order.can_send_report = False

    def action_send_report(self):
        self.ensure_one()
        self.report_sent = True

        self._ensure_report_link_main()
        print(f"[REPORT LINK] USING for email SO {self.name}: {self.report_link_main!r}")


        # default to the SYSTEM (link) template; switch to ..._manual if needed
        tmpl_xmlid = 'visio_tti_report_sending.mail_template_report_system'  # or 'visio_tti_report_sending.mail_template_report_manual'
        template = self.env.ref(tmpl_xmlid, raise_if_not_found=False) or self.env['mail.template'].search([
            ('model_id', '=', self.env.ref('sale.model_sale_order').id),
            ('name', 'ilike', 'TTI | System Test Report')
        ], limit=1)
        if not template:
            raise UserError("Custom email template not found. Ensure 'data/mail_templates.xml' is loaded.")

        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form', raise_if_not_found=False)

        to_emails = [
            (e.email or '').strip()
            for e in self.sale_email_ids
            if e.emails_to_receive in ('all', 'report') and e.email
        ]
        to_email_str = ', '.join([e for e in to_emails if e])
        cc_email = self.user_id.login if self.user_id and self.user_id.login else ''

        ctx = {
            'active_model': 'sale.order',
            'active_id': self.id,
            'active_ids': [self.id],

            'default_model': 'sale.order',
            'default_res_ids': [self.id],
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',

            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'default_email_values': {'email_to': to_email_str},
            'default_email_cc': cc_email,

            'from_send_report': True,

        }

        print("\n====================")
        print(f">>> Opening Send Report Email Wizard for SO: {self.name} (id={self.id})")
        print(f">>> TO: {to_email_str!r}")
        print(f">>> CC: {cc_email!r}")
        print(f">>> report_sent set to True ✅")
        print("====================\n")

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx,
        }

    def _notify_get_recipients_groups(self, message, model_description, msg_vals=None):
        """
        Inherit base notification logic but remove all access buttons
        (like 'View Quotation', 'Sign & Pay', etc.) ONLY when triggered
        from our custom 'action_send_report' email context.
        """
        groups = super()._notify_get_recipients_groups(
            message, model_description, msg_vals=msg_vals
        )

        if not self:
            return groups

        self.ensure_one()

        # 🚨 Only disable buttons when context indicates it's from 'Send Report'
        if self._context.get('from_send_report'):
            for group in groups:
                group_options = group[2]
                if 'has_button_access' in group_options:
                    group_options['has_button_access'] = False
                if 'button_access' in group_options:
                    group_options.pop('button_access', None)

        return groups