from odoo import models, fields, api


class TtiSoComponentBreakdown(models.Model):
    _name = "tti.so.component.breakdown"
    _description = "TTI Sale Order Component Breakdown"
    _order = "id desc, name"
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of

    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence", default=10)
    tti_sample = fields.Char(string="Sample")
    tti_material_no = fields.Char(string="Material No")
    tti_component_description = fields.Text(string="Component Description")
    tti_material_type = fields.Char(string="Material Type")
    tti_remarks = fields.Text(string="Remarks")
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Order Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(TtiSoComponentBreakdown, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(TtiSoComponentBreakdown, self).write(vals)

