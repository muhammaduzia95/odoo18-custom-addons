from odoo import models, fields, api


class TtiSiSubProductType(models.Model):
    _name = 'tti.si.product.type'
    _description = 'Tti Sample Information Product Type'
    _order = "id desc, name"
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of

    name = fields.Char(string='Product Type Name', required=True)
    tti_si_category = fields.Many2one('tti.si.category', string='Category', required=True, ondelete='cascade', domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(TtiSiSubProductType, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(TtiSiSubProductType, self).write(vals)
