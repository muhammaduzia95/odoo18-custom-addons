from odoo import models, fields, api, Command, _
import base64
from io import BytesIO
from PIL import Image
from odoo.exceptions import ValidationError

class ResCountryUpdate(models.Model):
    _inherit = "res.country"

    lims_code = fields.Char(string="LIMS Code", copy=False, readonly=False)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('code'):
                existing_codes = self.search([]).mapped('code')
                numeric_codes = [int(code) for code in existing_codes if code and code.isdigit()]
                next_code = str(max(numeric_codes) + 1) if numeric_codes else '1'
                vals['code'] = next_code

        return super(ResCountryUpdate, self).create(list_vals)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    sales_taxes = fields.Many2many(
        'account.tax',
        'state_sales_tax_rel',  # unique relation table name
        'state_id',
        'tax_id',
        string="Sales Taxes"
    )

    purchase_taxes = fields.Many2many(
        'account.tax',
        'state_purchase_tax_rel',  # unique relation table name
        'state_id',
        'tax_id',
        string="Purchase Taxes"
    )



class ResPartner(models.Model):
    _inherit = 'res.partner'

    code = fields.Char(string='Company Code', copy=False, readonly=False)

    tti_company_category = fields.Selection(
        [
            ('default', 'Default'),
            ('branch', 'Branch'),
            ('manufacture', 'Manufacture'),
            ('applicant', 'Applicant'),
            ('buyer', 'Buyer'),
            ('brand', 'Brand'),
            ('agent', 'Agent'),
        ], string='Company Category', default='default')
    tti_city_id = fields.Many2one('tti.city', string='City' , domain="[('company_id', '=', company_id)]")
    tti_city_zone_id = fields.Many2one('tti.city.zone', string='City Zone' , domain="[('company_id', '=', company_id)]")
    tti_test_packages = fields.Many2many('product.template', domain=[('test_type', '=', 'test_package')],
                                         string='Test Packages')
    sales_taxes = fields.Many2many(
        'account.tax',
        'partner_sales_tax_rel',
        'partner_id',
        'tax_id',
        string="Sales Taxes"
    )

    purchase_taxes = fields.Many2many(
        'account.tax',
        'partner_purchase_tax_rel',
        'partner_id',
        'tax_id',
        string="Purchase Taxes"
    )

    badge_id = fields.Char(string='Badge ID', compute='_compute_badge_id', store=True)

    @api.depends('employee_ids', 'employee_ids.barcode')
    def _compute_badge_id(self):
        Employee = self.env['hr.employee']
        for partner in self:
            employee = Employee.search([('related_partner_id', '=', partner.id)], limit=1)
            if employee:
                partner.badge_id = employee.barcode
            else:
                partner.badge_id = False

    # @api.onchange('state_id', 'state_id.sales_taxes', 'state_id.purchase_taxes')
    # def _compute_state_taxes(self):
    #     for partner in self:
    #         partner.sales_taxes = partner.state_id.sales_taxes
    #         partner.purchase_taxes = partner.state_id.purchase_taxes

    # discount_percent = fields.Float(
    #     string='Discount Percentage',
    #     default=0.0,
    #     help="Default discount percentage allowed to this user"
    # )

    # sale_order_definition = fields.PropertiesDefinition("Sale Order Properties Definition")

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            # if not vals.get('company_id'):
            #     raise ValidationError("Please add Company.")
            # if vals.get('sales_taxes'):
            #     raise ValidationError("Please add Sales Taxes.")
            if not vals.get('code'):
                existing_codes = self.search([]).mapped('code')
                numeric_codes = [int(code) for code in existing_codes if code and code.isdigit()]
                next_code = str(max(numeric_codes) + 1) if numeric_codes else '1'
                vals['code'] = next_code
        partners = super(ResPartner, self).create(list_vals)
        return partners

    # def write(self, vals):
        # for partner in self:
            # if not vals.get('company_id') and not partner.company_id:
            #     raise ValidationError("Please add Company.")
            # if not vals.get('sales_taxes') and not partner.sales_taxes:
            #     raise ValidationError("Please add Sales Taxes.")
        # return super(ResPartner, self).write(vals)

    @api.depends('name')
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for partner in self:
            partner.display_name = f"{partner.name}"
        return res


# class ResCompany(models.Model):
#     _inherit = 'res.company'
#
#     sale_order_definition = fields.PropertiesDefinition("Sale Order Property Structure")