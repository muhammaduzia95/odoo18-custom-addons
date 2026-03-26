from odoo import models, fields , api , _
from odoo.exceptions import UserError
from odoo.osv import expression
import requests

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    related_partner_id = fields.Many2one('res.partner', compute='_compute_related_partner', store=True, groups="hr.group_hr_user")

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        if 'barcode' in vals:
            for employee in self:
                if employee.related_partner_id:
                    employee.related_partner_id.sudo().write({'badge_id': vals['barcode']})
        return res

class ResPartner(models.Model):
    _inherit = 'res.partner'

    amount_credit_limit = fields.Monetary(string="Amount Credit Limit")
    credit_check = fields.Boolean(string="Credit Limit Check", default=False)
    strn = fields.Char(string="STRN")

    badge_id = fields.Char(string='Badge ID', compute='_compute_badge_id', store=True)

    # @api.depends('employee_ids', 'employee_ids.barcode')
    # def _compute_badge_id(self):
    #     Employee = self.env['hr.employee']
    #     for partner in self:
    #         employee = Employee.search([('related_partner_id', '=', partner.id)], limit=1)
    #         if employee:
    #             partner.badge_id = employee.barcode
    #         else:
    #             partner.badge_id = False

    @api.depends('employee_ids.barcode')
    def _compute_badge_id(self):
        Employee = self.env['hr.employee']

        for partner in self:
            employee = Employee.search([('work_contact_id', '=', partner.id)], limit=1)
            partner.badge_id = employee.barcode if employee else False

    @api.depends('badge_id')
    def _compute_display_name(self):
        for partner in self:
            if partner.badge_id:
                partner.display_name = f"[{partner.badge_id}] {partner.name}"
            else:
                partner.display_name = partner.name

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)

        if value and operator not in expression.NEGATIVE_TERM_OPERATORS:
            badge_domain = [('badge_id', operator, value)]

            if operator in ('ilike', '='):
                domain = expression.OR([domain, badge_domain])
            elif operator == 'in':
                domain = expression.OR([
                    domain,
                    *[[('badge_id', '=', val)] for val in value]
                ])

        return domain

    def action_unretract_reporting(self):
        for record in self:
            print("partner check" , record.credit_check)
            if record.credit_check:
                code = record.code
                try:
                    url = f"http://202.59.76.150/api/blockcompany/{code}/N"
                    response = requests.patch(url)
                    response_body = f"API Response: {response.status_code} - {response.text}"
                    print(response_body)
                    record.message_post(
                        body=response_body
                    )
                    if response.status_code == 200:
                        record.credit_check = False
                except Exception as e:
                    print(f"Error while calling API: {e}")

    def check_user_group_access(self):
        """Check if current user belongs to allowed group"""
        for record in self:
            if record.tti_company_category == 'manufacture':
                allowed_group = 'visio_tti_so_customize.group_tti_display_manufacturer'
                if not self.env.user.has_group(allowed_group):
                    raise UserError(_("You do not have permission to create/delete Manufacturers."))
            elif record.tti_company_category == 'applicant':
                allowed_group = 'visio_tti_so_customize.group_tti_display_applicant'
                if not self.env.user.has_group(allowed_group):
                    raise UserError(_("You do not have permission to create/delete Applicants."))
            elif record.tti_company_category == 'buyer':
                allowed_group = 'visio_tti_so_customize.group_tti_display_buyer'
                if not self.env.user.has_group(allowed_group):
                    raise UserError(_("You do not have permission to create/delete Buyers."))
            elif record.tti_company_category == 'agent':
                allowed_group = 'visio_tti_so_customize.group_tti_display_agents'
                if not self.env.user.has_group(allowed_group):
                    raise UserError(_("You do not have permission to create/delete Agents."))

    @api.model_create_multi
    def create(self, vals):
        record = super(ResPartner, self).create(vals)
        record.check_user_group_access()
        return record

    def unlink(self):
        for record in self:
            record.check_user_group_access()
        return super(ResPartner, self).unlink()

    def check_manufacturer_access(self):
        for record in self:
            if record.tti_company_category == 'manufacture':
                allowed_group = 'visio_tti_so_customize.group_tti_display_manufacturer'
                if not self.env.user.has_group(allowed_group):
                    raise UserError(_("You do not have permission to update Manufacturers."))

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        self.check_manufacturer_access()
        return res