from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    eobi_amount = fields.Float(digits="Payroll", string="EOBI Amount", currency_field='currency_id')
    eobi_employer_percent = fields.Float(string="EOBI Employer Percent")
    eobi_employee_percent = fields.Float(string="EOBI Employee/Worker Percent")
    eobi_employer = fields.Float(digits="Payroll",
        string="EOBI Employer",
        compute="_compute_eobi_employer",
        store=True,
        currency_field='currency_id',
    )
    eobi_employee = fields.Float(digits="Payroll",
        string="EOBI Employee/Worker",
        compute="_compute_eobi_employee",
        store=True,
        currency_field='currency_id',
    )

    eobi_employer_old = fields.Float(digits="Payroll", string="Old EOBI Employer", currency_field='currency_id')
    eobi_employee_old = fields.Float(digits="Payroll", string="Old EOBI Employee", currency_field='currency_id')

    eobi_employer_difference = fields.Float(digits="Payroll",
        string="EOBI Employer Difference",
        compute="_compute_eobi_employer_difference",
        currency_field='currency_id'
    )
    eobi_employee_difference = fields.Float(digits="Payroll",
        string="EOBI Employee/Worker Difference",
        compute="_compute_eobi_employee_difference",
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='company_id.currency_id'
    )

    def write(self, vals):
        for record in self:
            if 'eobi_amount' in vals or 'eobi_employer_percent' in vals:
                vals['eobi_employer_old'] = record.eobi_employer
            if 'eobi_amount' in vals or 'eobi_employee_percent' in vals:
                vals['eobi_employee_old'] = record.eobi_employee
        return super(HrPayrollStructure, self).write(vals)

    @api.depends('eobi_amount', 'eobi_employer_percent')
    def _compute_eobi_employer(self):
        for record in self:
            record.eobi_employer = (record.eobi_amount * (record.eobi_employer_percent * 100)) / 100 if record.eobi_amount else 0.0

    @api.depends('eobi_amount', 'eobi_employee_percent')
    def _compute_eobi_employee(self):
        for record in self:
            record.eobi_employee = (record.eobi_amount * (record.eobi_employee_percent * 100)) / 100 if record.eobi_amount else 0.0

    @api.depends('eobi_amount', 'eobi_employer_percent')
    def _compute_eobi_employer_difference(self):
        for record in self:
            new_value = (record.eobi_amount * (record.eobi_employer_percent * 100)) / 100 if record.eobi_amount else 0.0
            old_value = record.eobi_employer_old
            record.eobi_employer_difference = abs(new_value - old_value)

    @api.depends('eobi_amount', 'eobi_employee_percent')
    def _compute_eobi_employee_difference(self):
        for record in self:
            new_value = (record.eobi_amount * (record.eobi_employee_percent * 100)) / 100 if record.eobi_amount else 0.0
            old_value = record.eobi_employee_old
            record.eobi_employee_difference = abs(new_value - old_value)

    @api.constrains('eobi_amount', 'eobi_employer_percent', 'eobi_employee_percent')
    def _check_eobi_fields(self):
        for record in self:
            if record.eobi_amount <= 0:
                raise ValidationError(_("EOBI Amount must be greater than zero."))
            if (record.eobi_employer_percent * 100) < 0 or (record.eobi_employer_percent * 100) > 100:
                raise ValidationError(_("EOBI Employer Percent must be between 0 and 100."))
            if (record.eobi_employee_percent * 100) < 0 or (record.eobi_employee_percent * 100) > 100:
                raise ValidationError(_("EOBI Employee/Worker Percent must be between 0 and 100."))