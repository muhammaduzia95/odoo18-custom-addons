from odoo import models, fields, api

class TargetAchieved(models.Model):
    _name = 'target.achieve'
    _description = 'Target Achieved'

    name = fields.Char(string='Name')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
        domain="[('company_id', '=', company_id)]"
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        domain="[('company_id', '=', company_id)]"
    )
    region = fields.Many2one(
        'tti.city',
        string='Region',
        domain="[('company_id', '=', company_id)]"
    )
    city_zones = fields.Many2one(
        'tti.city.zone',
        string='City Zones',
        domain="[('company_id', '=', company_id),('tti_city_id','=',region)]"
    )
    categories = fields.Many2many(
        'tti.si.category',
        string='Categories',
        domain="[('company_id', '=', company_id)]"
    )
    target = fields.Float(string='Target')

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(TargetAchieved, self).create(list_vals)
