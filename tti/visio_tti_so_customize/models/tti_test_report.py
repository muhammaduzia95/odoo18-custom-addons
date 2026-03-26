from odoo import models, fields, api
from odoo.osv import expression

class TtiTestReports(models.Model):
    _name = "tti.test.report"
    _description = "TTI Test Reports"

    qty = fields.Float(string="Quantity", store=True, default=1.0)
    product_id = fields.Many2one('product.template', string="Product", ondelete='cascade')
    test_report = fields.Many2one('product.template', string="Test Report")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure",related='test_report.uom_id', readonly=True)
    total_cost = fields.Float(string="Total Price", compute='_compute_total_cost', readonly=True, store=True)

    @api.depends('test_report', 'qty', 'test_report.list_price')
    def _compute_total_cost(self):
        for record in self:
            if record.test_report:
                record.total_cost = record.test_report.list_price * record.qty
            else:
                record.total_cost = record.test_report.list_price


class TtiTestReportSoLine(models.Model):
    _name = "tti.test.report.so.line"
    _description = "TTI Test Report Sale Order Line"

    package_line_id = fields.Many2one('sale.order.line', string="Package Order Line", ondelete='cascade')
    unique_number = fields.Integer(
        string="Old API Global Unique ID",
        readonly=False,
        index=True,
        copy=False,
    )
    new_unique_number = fields.Integer(
        string="New API Global Unique ID",
        readonly=False,
        index=True,
        copy=False,
    )

    name = fields.Char(string="Name")
    qty = fields.Float(string="Quantity", default=1 , readonly=False)
    test_report = fields.Many2one('product.template', string="Test Report")
    package_id = fields.Many2one('product.template', string="Package")
    default_code = fields.Char(string="Code", readonly=True)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", related='test_report.uom_id', readonly=True)
    list_price = fields.Float(string="Rate", readonly=True)
    list_price_rate = fields.Float(string="Dollar Rate", compute='_compute_list_price_rate', readonly=True)
    list_price_usd = fields.Float(string="List Price USD", readonly=True)
    test_type = fields.Char(string="Test Type", readonly=True)
    total_cost = fields.Float(string="Total Price", compute='_compute_total_cost', readonly=True, store=True)
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Order Reference",
        required=True, ondelete='cascade', index=True, copy=False)

    sequence = fields.Integer(string="Sequence", default=10)
    dollar_exchange_rate = fields.Float(string="Dollar Exchange Rate", related='order_id.tti_dollar_exchange_rate', readonly=True)
    comments = fields.Char(string="Comments",)
    composites = fields.Char(string="Composites",)

    def _compute_list_price_rate(self):
        for record in self:
            # record.list_price_rate =  record.list_price / record.dollar_exchange_rate if record.dollar_exchange_rate else 1
            record.list_price_rate =  record.list_price / record.dollar_exchange_rate

    @api.depends('test_report', 'list_price', 'qty')
    def _compute_total_cost(self):
        for record in self:
            if record.test_report:
                record.total_cost = record.list_price * record.qty
            else:
                record.total_cost = record.list_price

    @api.model
    def _search_display_name(self, operator, value):
        # Default domain (e.g. display_name ilike value)
        domain = super()._search_display_name(operator, value)
        default_code_domain = [('default_code', operator, value)]
        combine = expression.OR if operator not in expression.NEGATIVE_TERM_OPERATORS else expression.AND
        return combine([domain, default_code_domain])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # if not vals.get('unique_number'):
            #     vals['unique_number'] = self.env['ir.sequence'].next_by_code('api.global.unique.id')

            if not vals.get('new_unique_number'):
                vals['new_unique_number'] = self.env['ir.sequence'].next_by_code('new.api.global.unique.id')

        return super().create(vals_list)



