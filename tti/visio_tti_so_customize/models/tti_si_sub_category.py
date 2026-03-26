from odoo import models, fields, api


class TtiSiSubCategory(models.Model):
    _name = 'tti.si.sub.category'
    _description = 'Tti Sample Information Sub Category'
    _order = "id desc, name"
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of

    name = fields.Char(string='Sub Category Name', required=True)
    code = fields.Char(string='Sub Category Code', copy=False , readonly=False)
    tti_si_category = fields.Many2one('tti.si.category', string='Category', required=True, ondelete='cascade', domain="[('company_id', '=', company_id)]")
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

        return super(TtiSiSubCategory, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(TtiSiSubCategory, self).write(vals)
