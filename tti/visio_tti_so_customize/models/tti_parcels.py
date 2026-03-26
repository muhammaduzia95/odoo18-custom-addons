from odoo.exceptions import ValidationError, UserError , AccessError
from odoo import models, fields, api, _


class TtiParcels(models.Model):
    _name = 'tti.parcels'
    _description = 'Tti Parcel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'tti_date desc, name desc, id desc'
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of
    _rec_names_search = ['name', 'tti_partner_id.name', 'tti_awb_number']

    name = fields.Char(string="Parcel ID", readonly=True, copy=False, default=lambda self: _('New'))
    tti_date = fields.Datetime(string='Date', default=fields.Datetime.now, copy=False)
    tti_courier_id = fields.Many2one('tti.parcel.courier', string='Courier' , domain="[('company_id', '=', company_id)]")
    tti_awb_number = fields.Char(string='AWB Number')
    tti_city_id = fields.Many2one('tti.city', string='City' , domain="[('company_id', '=', company_id)]")


    tti_partner_id = fields.Many2one('res.partner', string='Company Name',)
    tti_company = fields.Text(string='Company Name')


    tti_deliver_to = fields.Char(string='Deliver To')
    deliver_to_tti = fields.Many2one('hr.employee' , string='Deliver To')
    tti_category_name = fields.Char(string='Category')
    tti_time = fields.Float(string='Time')
    tti_description = fields.Text(string='Description')

    active = fields.Boolean('Active', default=True,help="If unchecked, it will allow you to hide the parcels without removing it.")
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Canceled'),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.root_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
            if not vals.get('user_id'):
                vals['user_id'] = self.env.user.id
            if not vals.get('name') or (vals.get('name') and vals.get('name') == 'New'):
                parcels_sequence = self.env['ir.sequence'].next_by_code('tti.parcels')
                vals['name'] = parcels_sequence
        if self.env.user.has_group('visio_tti_so_customize.group_read_only_parcel'):
            raise AccessError(_("You are not allowed to Create Parcels."))
        return super(TtiParcels, self).create(list_vals)

    def write(self, vals):
        if self.env.user.has_group('visio_tti_so_customize.group_read_only_parcel'):
            raise AccessError(_("You are not allowed to Update Parcels."))
        if not vals.get('user_id'):
            vals['user_id'] = self.env.user.id
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(TtiParcels, self).write(vals)

    def unlink(self):
        if not self.env.user.has_group('visio_tti_so_customize.group_delete_parcels'):
            raise AccessError(_("You are not allowed to delete Parcels."))
        if self.env.user.has_group('visio_tti_so_customize.group_read_only_parcel'):
            raise AccessError(_("You are not allowed to delete Parcels."))

        return super(TtiParcels, self).unlink()

    def button_cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    def button_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def action_confirm(self):
        self.ensure_one()
        self.state = 'posted'
