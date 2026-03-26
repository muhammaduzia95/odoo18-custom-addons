from odoo import models, fields, api, Command, _
from odoo.osv import expression
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class Currency(models.Model):
    _inherit = 'res.currency'

    def update_product_usd_to_list_price(self):
        self.ensure_one()
        products = self.env['product.template'].sudo().search([('type', '=', 'service'), ('test_type', 'in', ['test_report', 'test_package']), ('active', '=', True)])
        products._convert_usd_to_list_price()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    test_type = fields.Selection(
        [
            ('test_report', 'Test'),
            ('test_package', 'Package'),
        ],
        string='Test Type',
        help='Test Type (Test Report or Test Package)',
        default='test_report',
    )
    test_report_ids = fields.One2many(
        comodel_name='tti.test.report',
        inverse_name='product_id',
        string="Test Reports",
        copy=True, auto_join=True
    )
    tti_lims_test_id = fields.Char(string='Tti LIMS Test ID')
    tti_lims_package_id = fields.Char(string='Tti LIMS Package ID')
    tti_test_method = fields.Char(string='Test Method Name')
    tti_department_id = fields.Many2one('tti.si.department', string="Department")
    tti_test_group_id = fields.Many2one('tti.si.test.group', string="Test Group" , domain="[('company_id', '=', company_id)]")

    
    def check_user_group_access(self):
        """Check if current user belongs to allowed group"""
        for product in self:

            if product.purchase_ok:
                allowed_group = 'visio_tti_so_customize.group_tti_allow_purchase_product'  # Replace with your actual group XML ID
                if not self.env.user.has_group(allowed_group):
                    raise UserError(_("You do not have permission to perform this action on Purchase Products."))
            else:
                if product.test_type == 'test_report':
                    allowed_group = 'visio_tti_so_customize.group_tti_display_tests'  # Replace with your actual group XML ID
                    if not self.env.user.has_group(allowed_group):
                        raise UserError(_("You do not have permission to perform this action on Tests Products."))
                elif product.test_type == 'test_package':
                    allowed_group = 'visio_tti_so_customize.group_tti_display_packages'  # Replace with your actual group XML ID
                    if not self.env.user.has_group(allowed_group):
                        raise UserError(_("You do not have permission to perform this action on Packages Products."))


    @api.model_create_multi
    def create(self, vals):
        if self.env.user.name != 'Public user':
            self.check_user_group_access()
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        if self.env.user.name != 'Public user':
            self.check_user_group_access()
        return super(ProductTemplate, self).write(vals)

    def unlink(self):
        self.check_user_group_access()
        return super(ProductTemplate, self).unlink()

    # @api.depends('name', 'default_code', 'tti_test_method')
    # def _compute_display_name(self):
    #     res = super()._compute_display_name()
    #     for template in self:
    #         display_name = False
    #         if template.name:
    #             display_name = f"{template.default_code and '[%s]' % template.default_code or ''} {template.name} {template.tti_test_method and '(%s)' % template.tti_test_method or ''}"
    #         template.display_name = display_name
    #     return res

    @api.depends('name', 'default_code', 'tti_test_method')
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for template in self:
            _logger.info(f"user: {self.env.user.name}, name: {template.name}, default_code: {template.default_code}, test_method: {template.tti_test_method}")
            display_name = ''
            name = template.name or ''
            default_code = template.default_code or ''
            test_method = template.sudo().tti_test_method or ''
            display_name = f"{f'[{default_code}]' if default_code else ''} {name} {f'({test_method})' if test_method else ''}"
            template.sudo().display_name = display_name
        return res


    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)

        if self.env.context.get('search_product_product', bool(value)):
            combine = expression.OR if operator not in expression.NEGATIVE_TERM_OPERATORS else expression.AND
            domain = combine([domain, [('product_variant_ids', operator, value)]])

        method_domain = [('tti_test_method', operator, value)]
        domain = expression.OR([domain, method_domain])

        return domain

    list_price_usd = fields.Monetary(
        string="Sales Price $",
        currency_field='usd_currency_id'
    )

    usd_currency_id = fields.Many2one(
        'res.currency',
        string="USD Currency",
        compute='_compute_usd_currency',
        store=True
    )

    @api.depends('list_price', 'currency_id')
    def _compute_usd_currency(self):
        """Ensure USD currency is always set for list_price_usd"""
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        for record in self:
            record.usd_currency_id = usd_currency.id if usd_currency else False

    # @api.onchange('list_price')
    def _convert_list_price_to_usd(self):
        """Convert list_price to USD based on its current currency"""
        for record in self:
            if record.currency_id:
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                if usd_currency:
                    try:
                        if record.currency_id == usd_currency:
                            # If both are USD, keep them equal
                            record.list_price_usd = record.list_price
                        else:
                            # Convert to USD
                            record.list_price_usd = record.currency_id._convert(
                                record.list_price, usd_currency, record.env.company, fields.Date.today()
                            )
                    except Exception as e:
                        raise UserError(f"Error converting {record.currency_id.name} to USD: {str(e)}")

    @api.onchange('list_price_usd', 'list_price_usd.inverse_rate')
    def _convert_usd_to_list_price(self):
        """Convert list_price_usd back to the original currency of list_price"""
        for record in self:
            if record.currency_id:
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                if usd_currency:
                    try:
                        if record.currency_id == usd_currency:
                            # If both are USD, keep them equal
                            record.list_price = record.list_price_usd
                        else:
                            # Convert USD back to original currency
                            record.list_price = usd_currency._convert(
                                record.list_price_usd, record.currency_id, record.env.company, fields.Date.today()
                            )
                    except Exception as e:
                        raise UserError(f"Error converting USD to {record.currency_id.name}: {str(e)}")
