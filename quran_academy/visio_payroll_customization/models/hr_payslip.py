from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
from odoo.addons.web.controllers.export import ExcelExport
from odoo.http import request
from odoo import http
import json
import calendar
from datetime import datetime


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    two_third_rentpmonth = fields.Float(string="2/3 of Rate Per Month", default=0,
                                        compute="_compute_twothird_ratepmonth",
                                        store=True,
                                        digits='Payroll',
                                        currency_field='currency_id', copy=False)
    rate_per_month = fields.Float(digits="Payroll", string="Rate Per Month", default=0,
                                  store=True, currency_field='currency_id')
    other_duty = fields.Float(digits="Payroll", string="Other Duty", default=0, currency_field='currency_id')
    medical_availed = fields.Float(digits="Payroll", string="Medical Availed", default=0, currency_field='currency_id',
                                   copy=False)
    medical = fields.Float(digits="Payroll", string="Medical", default=0, currency_field='currency_id', copy=True)
    ext_arrear_night = fields.Float(digits="Payroll", string="Ext./Arrear/Night", default=0,
                                    currency_field='currency_id', copy=False)
    daily_wages = fields.Float(digits="Payroll", string="Daily Wages", default=0, currency_field='currency_id',
                               copy=False)
    rent_allow = fields.Float(digits="Payroll", string="Rent Allowance", default=0, currency_field='currency_id',
                              copy=False)
    other_deduction = fields.Float(digits="Payroll", string="Other Deduction", default=0, currency_field='currency_id')
    one_time_deduction = fields.Float(digits="Payroll", string="One Time Deduction", default=0,
                                      currency_field='currency_id')
    remaining_other_ded = fields.Float(digits="Payroll", string="Remaining Other Deduction", default=0,
                                      currency_field='currency_id')
    total_other_ded = fields.Float(digits="Payroll", string="Total Other Deductions", default=0,
                                   currency_field='currency_id', related="employee_id.total_other_ded")
    leave_in_cash = fields.Float(string="Leave in Cash", default=0, copy=False)
    over_time = fields.Float(string="Over Time", default=0, copy=False)
    wo_pay = fields.Float(string="Without Pay", default=0, copy=False)
    attendance_star = fields.Float(string="Attendance Star", default=0, copy=False)
    gross_total = fields.Float(digits="Payroll", string="Gross Total", currency_field='currency_id', copy=False)
    loan_recovery = fields.Float(digits="Payroll", string="Loan Recovery", default=0, currency_field='currency_id')
    adv_salary = fields.Float(digits="Payroll", string="Advance Salary", default=0, currency_field='currency_id',
                              copy=False)
    income_tax = fields.Float(digits="Payroll", string="Income Tax", default=0, currency_field='currency_id' ,copy=True)
    prov_fund = fields.Float(digits="Payroll", string="Provident Fund", default=0, currency_field='currency_id')
    tel_bill = fields.Float(digits="Payroll", string="Mess Bill", default=0, currency_field='currency_id',
                            copy=True)
    h_rent = fields.Float(digits="Payroll", string="House Rent", default=0, currency_field='currency_id')
    elec_gas_bill = fields.Float(digits="Payroll", string="Electricity/Gas Bill", default=0,
                                 currency_field='currency_id', copy=False)
    veh_charges = fields.Float(digits="Payroll", string="Vehicle Charges", default=0, currency_field='currency_id',
                               copy=False)
    other = fields.Float(digits="Payroll", string="Other Deductions", default=0, currency_field='currency_id')
    # eobi_worker = fields.Float(digits="Payroll", string="EOBI Worker", compute="_compute_eobi_values", store=True)
    # emp_eobi = fields.Float(digits="Payroll", string="EOBI Employer", compute="_compute_eobi_values", store=True)
    eobi_worker = fields.Float(digits="Payroll", string="EOBI Worker", store=True)
    emp_eobi = fields.Float(digits="Payroll", string="EOBI Employer", store=True)
    grand_total = fields.Float(digits="Payroll", string="Grand Total EOBI", compute="_compute_grand_total", store=True,
                               copy=False)
    total_deduction = fields.Float(digits="Payroll", string="Total Deduction", currency_field='currency_id', copy=False)
    net_payable = fields.Float(digits="Payroll", string="Net Payable", currency_field='currency_id', copy=False)
    eobi = fields.Boolean(
        string="EOBI",
        compute="_compute_eobi",
        store=True
    )
    leave_encash = fields.Boolean(
        string="Leave Encash 2/3",
        compute="_compute_leave_encash",
        store=True
    )
    paid_by = fields.Selection(
        selection=[
            ('cash', 'Cash'),
            ('cross_cheque', 'Cross Cheque'),
            ('deposited_in_bank', 'Deposited in Bank')
        ],
        string="Paid By",
        required=True,
        default='deposited_in_bank'
    )
    comments = fields.Text(string="Comments", copy=False)

    worker_code = fields.Char(string="Worker Code")
    department_code = fields.Char(string="Department Code")

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='company_id.currency_id'
    )
    master_department = fields.Char(string="Master Department", compute="_compute_master_first_child", store=True)
    first_child_dep = fields.Char(string="First Child Department", compute="_compute_master_first_child",
                                  store=True)
    department_name = fields.Char(string="Department", compute="_compute_master_first_child", store=True)

    employee_job_title = fields.Char(
        string="Designation",
        related="employee_id.job_title",
        store=True
    )
    employee_type_id = fields.Many2one(
        related="contract_id.type_id",
        store=True
    )


    eobi_num = fields.Char(string="EOBI_NO", related="employee_id.eobi_num",
                           store=True)

    eobi_emp_diff = fields.Float(digits="Payroll", string="Arrear EOBI Employer", currency_field='currency_id')
    eobi_worker_diff = fields.Float(digits="Payroll", string="Arrear EOBI Worker", currency_field='currency_id')
    grand_total_eobi_arrear = fields.Float(digits="Payroll", string="Grand Total EOBI Arrear",
                                           compute="_compute_grand_total",
                                           currency_field='currency_id', store=True)

    basic_total = fields.Float(digits="Payroll", string="Basic Total", currency_field='currency_id', store=True,
                               compute="_compute_basic_total")

    leave_in_cash_value = fields.Float(string="Leave Encash Value", digits="Payroll", copy=False)
    over_time_value = fields.Float(string="Over Time Value", digits="Payroll", copy=False)
    wo_pay_value = fields.Float(string="Without Pay Value", digits="Payroll", copy=False)
    attendance_star_value = fields.Float(string="Attendance Star Value", digits="Payroll", copy=False)

    special_allowance_qa = fields.Float(string="Special Allowance",copy=True)
    special_allowance_deduction = fields.Float(string="Special Allowance Deduction",)

    month = fields.Char(string="Month",compute="_compute_month",store=True, compute_sudo=True)

    @api.depends('date_from')
    def _compute_month(self):
        for slip in self:
            if slip.date_from:
                # ensure date is datetime
                date_val = fields.Date.from_string(slip.date_from)
                slip.month = date_val.strftime("%B-%Y")
            else:
                slip.month = ""



    @api.onchange('special_allowance_qa')
    def _onchange_special_allowance_qa(self):
        for rec in self:
            rec.tel_bill = rec.special_allowance_qa



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            employee_id = vals.get('employee_id')
            contract_id = vals.get('contract_id')
            if not vals.get('number'):
                vals['number'] = self.env['ir.sequence'].next_by_code('salary.slip')
            if employee_id:
                employee = self.env['hr.employee'].browse(employee_id)
                vals['worker_code'] = employee.employee_sequence
                vals['department_code'] = employee.department_sequence

                # Fetch previous done payslip for this employee
                previous_payslip = self.env['hr.payslip'].search(
                    [('employee_id', '=', employee_id), ('state', '=', 'done')],
                    order='date_from desc',
                    limit=1
                )

                # Copy recurring fields if not already in vals
                if previous_payslip:
                    for field_name in ['medical', 'special_allowance_qa', 'tel_bill', 'income_tax']:
                        if field_name not in vals or not vals.get(field_name):
                            vals[field_name] = previous_payslip[field_name]


                previous_payslips = self.env['hr.payslip'].search(
                    [('employee_id', '=', employee_id), ('state', '=', 'done')])
                medical_availed = sum(payslip.medical for payslip in previous_payslips)
                other_ded = sum(payslip.other_deduction for payslip in previous_payslips)
                vals['remaining_other_ded'] = employee.total_other_ded - other_ded
                vals['medical_availed'] = medical_availed

            if contract_id:
                employee = self.env['hr.employee'].browse(employee_id)
                # vals['rate_per_month'] = employee.contract_id.wage
                # vals['loan_recovery'] = employee.contract_id.loan_recovery

        return super(HrPayslip, self).create(vals)

    def write(self, vals):
        for record in self:
            if 'eobi' in vals:
                record.employee_id.eobi = vals['eobi']
            if 'leave_encash' in vals:
                record.employee_id.leave_encash = vals['leave_encash']
            if 'contract_id' in vals:
                record.rate_per_month = record.contract_id.wage
            if 'loan_recovery' in vals:
                record.contract_id.loan_recovery_source = 'payslip'
            if 'rate_per_month' in vals:
                record.contract_id.wage_source = 'payslip'

            # New logic: auto-copy recurring fields if in draft and not provided
            if record.state == 'draft':
                previous_payslip = self.env['hr.payslip'].search(
                    [('employee_id', '=', record.employee_id.id), ('state', '=', 'done')],
                    order='date_from desc',
                    limit=1
                )
                if previous_payslip:
                    for field_name in ['medical', 'special_allowance_qa', 'tel_bill', 'income_tax']:
                        if field_name not in vals or not vals.get(field_name):
                            # Only fill if current value is empty/zero
                            if not getattr(record, field_name):
                                vals[field_name] = previous_payslip[field_name]

        return super(HrPayslip, self).write(vals)

    @api.depends('rate_per_month')
    def _compute_twothird_ratepmonth(self):
        for record in self:
            record.two_third_rentpmonth = (record.rate_per_month * 2 / 3) if record.rate_per_month else 0.0

    @api.depends('rate_per_month', 'other_duty')
    def _compute_basic_total(self):
        for record in self:
            record.basic_total = record.rate_per_month + record.other_duty

    @api.depends('employee_id.department_id')
    def _compute_master_first_child(self):
        for record in self:
            record.department_name = record.employee_id.department_id.name
            parent_path = record.employee_id.department_id.parent_path
            if parent_path:
                parent_ids = parent_path.split('/')
                master_department = self.env['hr.department'].browse(int(parent_ids[0]))
                first_child_dep = self.env['hr.department'].browse(int(parent_ids[1])) if len(parent_ids) > 1 and \
                                                                                          parent_ids[1] else False
                record.master_department = master_department.name
                record.first_child_dep = first_child_dep.name
            else:
                record.master_department = False
                record.first_child_dep = False

    # @api.depends('eobi', 'struct_id')
    # def _compute_eobi_values(self):
    #     for record in self:
    #         if record.state == 'draft':
    #             if record.eobi and record.struct_id:
    #                 record.eobi_worker = record.struct_id.eobi_employee
    #                 record.emp_eobi = record.struct_id.eobi_employer
    #             else:
    #                 record.eobi_worker = 0
    #                 record.emp_eobi = 0

    @api.depends('eobi_worker', 'emp_eobi')
    def _compute_grand_total(self):
        for record in self:
            record.grand_total = record.eobi_worker + record.emp_eobi
            record.grand_total_eobi_arrear = record.eobi_emp_diff + record.eobi_worker_diff

    @api.depends('employee_id.eobi', 'state')
    def _compute_eobi(self):
        for record in self:
            if record.state == 'draft':
                record.eobi = record.employee_id.eobi
            else:
                record.eobi = record.eobi

    @api.depends('employee_id.leave_encash', 'state')
    def _compute_leave_encash(self):
        for record in self:
            if record.state == 'draft':
                record.leave_encash = record.employee_id.leave_encash
            else:
                record.leave_encash = record.leave_encash

    def compute_sheet(self):
        result = super(HrPayslip, self).compute_sheet()
        for payslip in self:
            for line in payslip.line_ids:
                if line.category_id.code == 'NET':
                    payslip.net_payable = line.total
                elif line.category_id.code == 'DED':
                    total_deduction = sum(
                        line.total for line in payslip.line_ids if line.category_id.code == 'DED'
                    )
                    total_deduction += payslip.special_allowance_deduction or 0.0
                    print(payslip.special_allowance_deduction, "<-----")
                    payslip.total_deduction = abs(total_deduction)
                elif line.category_id.code == 'GROSS':
                    payslip.gross_total = line.total
                elif line.category_id.code == 'LE':
                    payslip.leave_in_cash_value = line.total
                elif line.category_id.code == 'OT':
                    payslip.over_time_value = line.total
                elif line.category_id.code == 'ASTAR':
                    payslip.attendance_star_value = abs(line.total)
                elif line.category_id.code == 'WP':
                    payslip.wo_pay_value = abs(line.total)

            # if payslip.struct_id:
            #     payslip.eobi_emp_diff = payslip.struct_id.eobi_employer_difference
            #     payslip.eobi_worker_diff = payslip.struct_id.eobi_employee_difference

            if payslip.loan_recovery != payslip.contract_id.loan_recovery and payslip.state == 'draft':
                if payslip.contract_id.loan_recovery_source == 'contract':
                    payslip.loan_recovery = payslip.contract_id.loan_recovery
                if payslip.contract_id.loan_recovery_source == 'payslip':
                    payslip.contract_id.loan_recovery = payslip.loan_recovery

            employee_id = payslip.employee_id
            if payslip.state == 'draft' and employee_id:
                employee_id.wage = payslip.rate_per_month
                employee_id.other_duty = payslip.other_duty
                employee_id.loan_recovery = payslip.loan_recovery

            if payslip.state == 'draft':
                previous_payslips = self.env['hr.payslip'].search(
                    [('employee_id', '=', payslip.employee_id.id), ('state', '=', 'done')])
                other_ded = sum(previous_payslips.mapped('other_deduction'))
                payslip.remaining_other_ded = payslip.total_other_ded - other_ded - payslip.other_deduction

            if payslip.rate_per_month != payslip.contract_id.wage and payslip.state == 'draft':
                if payslip.contract_id.wage_source == 'contract':
                    payslip.rate_per_month = payslip.contract_id.wage
                if payslip.contract_id.wage_source == 'payslip':
                    payslip.contract_id.wage = payslip.rate_per_month

        return result

    @api.constrains(
        'other_duty', 'medical', 'ext_arrear_night', 'daily_wages', 'rent_allow',
        'other_deduction', 'loan_recovery', 'adv_salary', 'income_tax', 'prov_fund',
        'tel_bill', 'h_rent', 'elec_gas_bill', 'veh_charges', 'other', 'attendance_star'
    )
    def _check_negative_values(self):
        for record in self:
            for field_name in [
                'other_duty', 'medical', 'ext_arrear_night', 'daily_wages', 'rent_allow',
                'other_deduction', 'loan_recovery', 'adv_salary', 'income_tax', 'prov_fund',
                'tel_bill', 'h_rent', 'elec_gas_bill', 'veh_charges', 'other', 'attendance_star'
            ]:
                if getattr(record, field_name) < 0:
                    raise ValidationError(
                        _("The value of Allowance/Deduction cannot be negative.")
                    )

    def _compute_details_by_salary_rule_category(self):
        for payslip in self:
            payslip.details_by_salary_rule_category = payslip.mapped('line_ids').filtered(
                lambda line: line.category_id and (line.total != 0))

    @api.model
    def retrieve_dashboard(self):
        """ Fetches statistics for the Payslip dashboard """
        total_payslips = self.search_count([])
        draft_payslips = self.search_count([('state', '=', 'draft')])
        confirmed_payslips = self.search_count([('state', '=', 'done')])

        return {
            "total_payslips": total_payslips,
            "draft_payslips": draft_payslips,
            "confirmed_payslips": confirmed_payslips,
        }


class CustomExcelExport(ExcelExport):

    @http.route('/web/export/xlsx', type='http', auth='user')
    def web_export_xlsx(self, data):
        try:
            data_dict = json.loads(data)
            context = data_dict.get('context', {}) or {}
            print("context", context)

            export_name = context.get('export_filename')
            if export_name == 'Paid By Summary':
                custom_filename = f"Paid By Summary"
            elif export_name == 'Paid By Summary Category':
                custom_filename = f"Paid By Summary Category"
            elif export_name == 'Overtime This Month':
                custom_filename = f"Overtime This Month"
            elif export_name == 'Loan This Month':
                custom_filename = f"Loan This Month"
            elif export_name == 'Medical This Month':
                custom_filename = f"Medical This Month"
            elif export_name == 'Without Pay This Month':
                custom_filename = f"Without Pay This Month"
            elif export_name == 'EOBI This Month':
                custom_filename = f"EOBI This Month"
            elif export_name == 'EOBI Arrear This Month':
                custom_filename = f"EOBI Arrear This Month"
            elif export_name == 'Salary Statement This Month':
                custom_filename = f"Salary Statement This Month"
            elif export_name == 'Pay Receiving Cash List':
                custom_filename = f"Pay Receiving Cash List"
            elif export_name == 'Pay Receiving Bank List':
                custom_filename = f"Pay Receiving Bank List"
            else:
                custom_filename = None

            self._custom_filename = custom_filename

            return self.base(data)
        except Exception as exc:
            print("Exception during request handling.")
            payload = json.dumps({
                'code': 200,
                'message': "Odoo Server Error",
                'data': http.serialize_exception(exc)
            })
            raise InternalServerError(payload) from exc

    def filename(self, base):
        if hasattr(self, '_custom_filename') and self._custom_filename:
            return self._custom_filename
        return super().filename(base)


