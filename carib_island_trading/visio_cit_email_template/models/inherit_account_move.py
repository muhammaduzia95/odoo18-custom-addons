from odoo import models


class AccountMoveSendWizard(models.TransientModel):
    _inherit = 'account.move.send.wizard'

    TANISHA_TPL = (
        'visio_cit_email_template.'
        'email_template_tanisha_invoice_new_customer'
    )

    def _get_default_mail_attachments_widget(
        self, move, mail_template,
        invoice_edi_format=None, extra_edis=None, pdf_report=None,
    ):
        # Odoo default list
        widget = super()._get_default_mail_attachments_widget(
            move, mail_template,
            invoice_edi_format=invoice_edi_format,
            extra_edis=extra_edis,
            pdf_report=pdf_report,
        )

        tanisha_tpl = self.env.ref(self.TANISHA_TPL, raise_if_not_found=False)
        if not (mail_template and tanisha_tpl and mail_template.id == tanisha_tpl.id):
            return widget                       # not our template

        print(f"\n🔧 Wizard rebuild for {move.name}")

        tanisha_ids = set(move.attachment_ids_in.ids)
        seen = set()
        final = []

        # ------------------------------------------------------------------
        # 1) keep only items NOT auto-generated PDF and NOT Tanisha dupes
        # ------------------------------------------------------------------
        for item in widget:
            att_id = item.get('id')
            if not att_id:
                continue
            if att_id in tanisha_ids:           # drop old Tanisha copies
                continue
            if not item.get('manual'):          # drop auto PDF / EDI
                continue
            if att_id in seen:                  # paranoid uniqueness
                continue
            seen.add(att_id)
            final.append(item)

        # ------------------------------------------------------------------
        # 2) append Tanisha attachments once (no manual flag!)
        # ------------------------------------------------------------------
        for att in move.attachment_ids_in:
            if att.id in seen:
                continue
            final.append({
                'id': att.id,
                'name': att.name,
                'url': f'/web/content/{att.id}?download=true',
                'mimetype': att.mimetype,
                # no 'manual': True  → prevents duplicate reinjection
            })
            seen.add(att.id)

        print("✅ Final attachment IDs:", list(seen))
        return final
