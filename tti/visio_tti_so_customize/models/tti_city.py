from odoo import models, fields, api


class TtiCity(models.Model):
    _name = 'tti.city'
    _description = 'Tti City'
    _order = "name"
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of

    name = fields.Char(string='City Name', required=True)
    code = fields.Char(string='City Code', copy=False , readonly=False)
    country_id = fields.Many2one('res.country', string='Country', required=True,
                                 default=lambda self: self.env.company.country_id)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id

            if not vals.get('code'):
                existing_codes = self.search([]).mapped('code')
                numeric_codes = [int(code) for code in existing_codes if code and code.isdigit()]
                next_code = str(max(numeric_codes) + 1) if numeric_codes else '1'
                vals['code'] = next_code

        return super(TtiCity, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(TtiCity, self).write(vals)
