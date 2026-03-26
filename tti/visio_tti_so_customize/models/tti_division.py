from odoo import models, fields, api

class TtiDivision(models.Model):
    _name = 'tti.division'
    _description = 'Tti Division'

    name = fields.Char(string='Name')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(TtiDivision, self).create(list_vals)
