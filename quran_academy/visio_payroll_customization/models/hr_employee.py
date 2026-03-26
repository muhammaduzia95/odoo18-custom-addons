from odoo import api, fields, models, _
import re
from odoo.exceptions import ValidationError, AccessError
from odoo.osv import expression

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    name_urdu = fields.Char(string="Name Urdu")
    date_of_app = fields.Date(string="Date of App.")
    card_date = fields.Date(string="Card Date")
    blood_group = fields.Char(string="Blood Group")
    father_name = fields.Char(string="Father's Name")
    nicno = fields.Char(string="NICNO")
    marks_of_indity = fields.Char(string="Marks of Indity")
    card_validity_date = fields.Date(string="Card Validity Date")
    eobi_num = fields.Char(string="EOBI_NO")
    date_exit_eobi = fields.Date(string="Date Exit EOBI")
    date_leaving = fields.Date(string="Date of leaving")
    id_card = fields.Boolean(string="ID Card", default=False)
    eobi = fields.Boolean(string="EOBI", default=False)
    leave_encash = fields.Boolean(string="Leave Encash 2/3", default=False)
    acc_num = fields.Char(string="Account NO")

    employee_sequence = fields.Char(string="Worker Code", copy=False)

    employee_number = fields.Char(string="Employee Number", readonly=True, copy=False)

    department_sequence = fields.Char(
        string="Department Sequence",
        related="department_id.department_sequence",
        readonly=True,
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='company_id.currency_id'
    )
    date_start = fields.Date(string="Contract Start Date")
    date_end = fields.Date(string="Contract End Date")
    wage = fields.Float(digits="Payroll", string="Rate Per Month", default=0,
                                     store=True, currency_field='currency_id')
    other_duty = fields.Float(digits="Payroll", string="Other Duty", default=0,
                                     store=True, currency_field='currency_id')
    total_other_ded = fields.Float(digits="Payroll", string="Total Other Deduction", default=0,
                              store=True, currency_field='currency_id')
    loan_recovery = fields.Float(digits="Payroll", string="Loan Recovery", default=0,
                                 store=True, currency_field='currency_id')
    medical = fields.Float(digits="Payroll", string="Medical", default=0, currency_field='currency_id', store=True)
    special_allowance_qa = fields.Float(string="Special Allowance",store=True)




    @api.model_create_multi
    def create(self, vals_list):
        pakistan = self.env['res.country'].search([('name', '=', 'Pakistan')], limit=1)
        for vals in vals_list:
            if pakistan:
                vals['country_id'] = pakistan.id
                vals['country_of_birth'] = pakistan.id
                vals['private_country_id'] = pakistan.id

            if not vals.get('employee_sequence'):
                vals['employee_sequence'] = self.env['ir.sequence'].next_by_code('hr.employee.number').replace('EMP',
                                                                                                               'EMP/')
        employees = super(HrEmployee, self).create(vals_list)
        for employee in employees:
            if employee.id_card and employee.employee_sequence:
                employee.barcode = employee.employee_sequence
        return employees

    def write(self, vals):
        sync_fields = ['date_start', 'date_end', 'wage', 'loan_recovery']

        if any(field in vals for field in sync_fields):
            for employee in self:
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'open')
                ], limit=1)

                if not contract:
                    contract = self.env['hr.contract'].search([
                        ('employee_id', '=', employee.id),
                        ('state', '=', 'draft')
                    ], limit=1)

                update_vals = {}
                for field in sync_fields:
                    if field in vals:
                        update_vals[field] = vals[field]

                if contract and update_vals:
                    contract.write(update_vals)

        if 'id_card' in vals and vals['id_card']:
            for employee in self:
                if employee.employee_sequence and employee.barcode == False:
                    employee.barcode = employee.employee_sequence

        return super(HrEmployee, self).write(vals)

    @api.depends('name', 'employee_sequence')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.employee_sequence}] {record.name}"

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if self.env.context.get('search_employee', bool(value)):
            combine = expression.OR if operator not in expression.NEGATIVE_TERM_OPERATORS else expression.AND
            domain = combine([domain, [('employee_sequence', operator, value)]])
        return domain

    @api.constrains('barcode')
    def _verify_barcode(self):
        for employee in self:
            if employee.barcode:
                if not (re.match(r'^[A-Za-z0-9/]+$', employee.barcode) and len(employee.barcode) <= 25):
                    raise ValidationError(
                        _("The Badge ID must be alphanumeric without any accents and no longer than 25 characters."))

    def action_create_contracts(self):
        for employee in self:
            structure = self.env['hr.payroll.structure'].search([('name', '=', 'Quran Academy Salary Structure')],
                                                                limit=1)
            contract = self.env['hr.contract'].create({
                'name': f"Contract for {employee.name}",
                'employee_id': employee.id,
                'department_id': employee.department_id.id if employee.department_id else False,
                'struct_id': structure.id,
                'state': 'open',
                'job_id': employee.job_id.id,
                'wage': employee.wage,
                'date_start': employee.date_start,
                'date_end': employee.date_end,
            })
