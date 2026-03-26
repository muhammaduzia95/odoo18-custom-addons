# models/res_partner_user_ids.py
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    user_ids = fields.Many2many('res.users', 'res_partner_res_users_rel', 'partner_id', 'user_id',
                                string='Salespersons')

    # @api.model
    # def _my_contacts_domain(self):
    #     if self.env.user.has_group('visio_cit_sale_customization.group_user_on_contacts'):
    #         return [
    #             '|',
    #             ('user_ids', '=', False),
    #             ('user_ids', 'in', [self.env.user.id]),
    #         ]
    #     return []
    #
    # @api.model
    # def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None, **kwargs):
    #     args = (args or []) + self._my_contacts_domain()
    #     return super()._search(
    #         args,
    #         offset=offset,
    #         limit=limit,
    #         order=order,
    #         access_rights_uid=access_rights_uid,
    #)
