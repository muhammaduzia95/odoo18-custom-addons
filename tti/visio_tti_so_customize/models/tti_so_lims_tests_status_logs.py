from odoo import models, fields, api


class SaleOrderLIMSTestsStatusLogs(models.Model):
    _name = 'tti.so.lims.tests.status.logs'
    _description = 'Sale Order LIMS Tests Status Logs'
    _order = "id desc, name"
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of

    name = fields.Char(string='Log Name')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    tti_lims_test_id = fields.Char(string='Tti LIMS Test ID')
    order_id = fields.Char(string="Sale Order ID")
    product_name = fields.Char(string="Test Name")
    status = fields.Char(string="Status")
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(SaleOrderLIMSTestsStatusLogs, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(SaleOrderLIMSTestsStatusLogs, self).write(vals)
