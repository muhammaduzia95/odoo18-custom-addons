from odoo import models, fields, api


class TtiSiCategory(models.Model):
    _name = 'tti.si.category'
    _description = 'Tti Sample Information Category'
    _order = "id desc, name"
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of

    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Category Code', copy=False , readonly=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    division_id = fields.Many2one('tti.division', string='Division', required=True, domain="[('company_id', '=', company_id)]")
    sub_category_ids = fields.One2many('tti.si.sub.category', 'tti_si_category', check_company=True , domain="[('company_id', '=', company_id)]")
    product_type_ids = fields.One2many('tti.si.product.type', 'tti_si_category', check_company=True , domain="[('company_id', '=', company_id)]")
    category_type = fields.Selection([
        ('petroleum', 'Petroleum'),
        ('pharma', 'Pharma'),
        ('food', 'Food'),
        ('inspection', 'Inspection'),
        ('wne', 'WnE'),
    ], string='Category Type')

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

        return super(TtiSiCategory, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(TtiSiCategory, self).write(vals)
