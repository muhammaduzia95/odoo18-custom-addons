from odoo import models, fields, api


class TtiPiBrand(models.Model):
    _name = 'tti.pi.brand'
    _description = 'Tti Party Information Brand'
    _order = "id desc, name"
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of

    name = fields.Char(string='Brand Name', required=True)
    email = fields.Char(string='Email')
    test_packages = fields.Many2many('product.template', domain=[('test_type', '=', 'test_package')], string='Test Packages')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(TtiPiBrand, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(TtiPiBrand, self).write(vals)
