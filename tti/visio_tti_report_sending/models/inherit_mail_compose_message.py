# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_report_sending\models\inherit_mail_compose_message.py
from odoo import models, fields, api
from odoo.tools import email_split

def _dedup(emails):
    out, seen = [], set()
    for e in (emails or []):
        e = (e or '').strip()
        if e and e not in seen:
            seen.add(e)
            out.append(e)
    return out

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    # Visible in the wizard
    email_cc = fields.Char(string="CC")

    def _get_mail_values(self, res_ids):
        """
        Ensure the CC entered/shown in the wizard is copied into the actual outgoing mail.
        Add prints so we can see exactly what's happening.
        """
        mail_values = super()._get_mail_values(res_ids)

        typed_cc_raw = (self.email_cc or '')
        ctx_cc_raw = (self.env.context.get('default_email_cc') or '')

        print("=== _get_mail_values CALLED ===")
        print(f"wizard.email_cc(raw)={typed_cc_raw!r} | ctx.default_email_cc(raw)={ctx_cc_raw!r}")

        # normalize punctuation
        typed_cc = typed_cc_raw.replace(';', ',')
        ctx_cc = ctx_cc_raw.replace(';', ',')

        # split + dedup
        typed_cc_list = _dedup(email_split(typed_cc)) if typed_cc else []
        ctx_cc_list = _dedup(email_split(ctx_cc)) if ctx_cc else []

        # prefer what the user typed in the wizard, else fall back to context default
        cc_list = typed_cc_list or ctx_cc_list
        print(f"typed_cc_list={typed_cc_list} | ctx_cc_list={ctx_cc_list} | chosen cc_list={cc_list}")

        for rid, vals in mail_values.items():
            before_cc_raw = vals.get('email_cc') or ''
            before_cc_list = _dedup(email_split(before_cc_raw.replace(';', ','))) if before_cc_raw else []
            merged = _dedup(before_cc_list + cc_list)
            print(f"[BEFORE] rid={rid} email_to={vals.get('email_to')} email_cc={before_cc_raw} recipient_ids={vals.get('recipient_ids')}")
            print(f"[MERGE ] rid={rid} existing_cc_list={before_cc_list} + new_cc_list={cc_list} -> merged={merged}")
            vals['email_cc'] = ','.join(merged) if merged else False
            print(f"[AFTER ] rid={rid} email_to={vals.get('email_to')} email_cc={vals.get('email_cc')} recipient_ids={vals.get('recipient_ids')}")
            mail_values[rid] = vals

        return mail_values

    def action_send_mail(self):
        """
        Add prints and pass the (possibly edited) wizard CC in context for extra safety.
        """
        print("=== action_send_mail CALLED ===")
        print(f"wizard.email_cc={self.email_cc!r} | model={self.model} | res_ids={self.res_ids}")
        ctx = dict(self.env.context or {})
        ctx['compose_email_cc'] = (self.email_cc or '')
        return super(MailComposeMessage, self.with_context(ctx)).action_send_mail()


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def create(self, vals_list):
        single = isinstance(vals_list, dict)
        batch = [vals_list] if single else list(vals_list)
        print(f"=== mail.mail.create CALLED === count={len(batch)} | ctx.compose_email_cc={self.env.context.get('compose_email_cc')!r}")

        out = []
        for i, vals in enumerate(batch):
            print(f"[CREATE BEFORE {i}] model={vals.get('model')} res_id={vals.get('res_id')} "
                  f"email_to={vals.get('email_to')} email_cc={vals.get('email_cc')} recipient_ids={vals.get('recipient_ids')}")

            # If CC not set by _get_mail_values for any reason, try to inject from context as a fallback
            if not vals.get('email_cc'):
                ctx_cc_raw = (self.env.context.get('compose_email_cc') or '')
                ctx_cc = ctx_cc_raw.replace(';', ',')
                ctx_cc_list = _dedup(email_split(ctx_cc)) if ctx_cc else []
                if ctx_cc_list:
                    vals['email_cc'] = ','.join(ctx_cc_list)
                    print(f"[INJECT CC {i}] Injected CC from context: {vals['email_cc']}")

            print(f"[CREATE AFTER  {i}] email_to={vals.get('email_to')} email_cc={vals.get('email_cc')} recipient_ids={vals.get('recipient_ids')}")
            out.append(vals)

        res = super().create(out)
        return res[0] if single else res

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None,
              alias_domain_id=None, **kwargs):
        for m in self:
            recips = [p.email for p in m.recipient_ids if p.email]
            print("=== mail.mail._send === "
                  f"id={m.id} model={m.model} res_id={m.res_id} "
                  f"email_to={m.email_to} email_cc={m.email_cc} recipients(m2m)={recips}")
        return super()._send(auto_commit=auto_commit, raise_exception=raise_exception,
                             smtp_session=smtp_session, alias_domain_id=alias_domain_id, **kwargs)
