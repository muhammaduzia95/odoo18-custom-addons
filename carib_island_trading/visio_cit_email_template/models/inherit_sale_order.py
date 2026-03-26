# carib_island_trading\visio_cit_email_templates\models\inherit_sale_order.py
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        action = super().action_quotation_send()

        if len(self) == 1:
            tmpl = self.env.ref(
                'visio_cit_email_template.email_template_tanisha_new_customer',
                raise_if_not_found=False,
            )
            if tmpl:
                ctx = dict(action.get('context', {}))
                ctx.update({
                    'default_use_template': True,
                    'default_template_id': tmpl.id,
                })
                action['context'] = ctx
        return action


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def _generate_template(self, res_ids, fields, **kwargs):
        result = super()._generate_template(res_ids, fields, **kwargs)

        tanisha_tmpl = self.env.ref(
            'visio_cit_email_template.email_template_tanisha_new_customer',
            raise_if_not_found=False,
        )
        if tanisha_tmpl and self.id == tanisha_tmpl.id and 'attachment_ids' in fields:
            so_model = self.env['sale.order']
            for res_id in res_ids:
                order = so_model.browse(res_id)
                if order.attachment_ids_so:
                    current = result[res_id].get('attachment_ids') or []
                    result[res_id]['attachment_ids'] = list(
                        set(current + order.attachment_ids_so.ids)
                    )
        return result
