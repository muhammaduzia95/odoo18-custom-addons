# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_salary_report\wizard\salary_report_wizard.py
from odoo import models, fields
import io
import base64
import xlsxwriter
import calendar
from datetime import date
import calendar
from collections import defaultdict


class TTISalaryReportWizard(models.TransientModel):
    _name = "tti.salary.report.wizard"
    _description = "TTI Salary Report Wizard"

    def _default_date_from(self):
        today = fields.Date.context_today(self)
        return today.replace(day=1)

    def _default_date_to(self):
        today = fields.Date.context_today(self)
        last_day = calendar.monthrange(today.year, today.month)[1]
        return today.replace(day=last_day)

    date_from = fields.Date(string="From Date", required=True, default=_default_date_from, )
    date_to = fields.Date(string="To Date", required=True, default=_default_date_to, )

    # Generate Excel report
    def action_generate_excel(self):
        """Trigger Excel report"""
        self.ensure_one()
        # Figure out number of days in month (for gross salary calculation)
        month_days = calendar.monthrange(self.date_from.year, self.date_from.month)[1]

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Salary Report')

        # Formats
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        subtitle_format = workbook.add_format({'font_size': 12, })
        subtitle_format_b = workbook.add_format({'font_size': 12, 'bold': True, })
        header_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        cell_format = workbook.add_format({'border': 1})
        center_format = workbook.add_format({'border': 1, 'align': 'center'})  # For Sr.No
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0'})  # For numeric values

        # Fetch payslips in date range
        domain = [
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('state', '=', 'done'),
        ]
        payslips = self.env['hr.payslip'].search(domain)

        # Row 1–2 headings
        worksheet.merge_range(0, 0, 0, 18, 'Tti Testing Laboratories', title_format)
        batch_names = ", ".join(set(payslips.mapped("payslip_run_id.name")))
        worksheet.write(1, 0, "Payslip Batch", subtitle_format_b)
        worksheet.write(1, 1, batch_names or '', subtitle_format)

        # Column headers
        headers = [
            "Branch Name", "Department Name", "Sr.No", "Emp.No.", "Name", "Designation",
            "Gross Salary", "Paid Days", "Gross salary for the month", "Other Allowance",
            "Total Gross Salary Payable", "Advance", "Loan", "EOBI", "Mess", "Tax",
            "Other", "Total", "Net Salary Payable"
        ]

        worksheet.set_column(8, 8, 25)  # Column I
        worksheet.set_column(10, 10, 25)  # Column K

        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)  # row 4 (index 3)

        # Fetch payslips in date range
        domain = [
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('state', '=', 'done'),
        ]
        payslips = self.env['hr.payslip'].search(domain)

        row = 4  # start writing after header
        sr_no = 1

        for slip in payslips:
            emp = slip.employee_id
            contract = slip.contract_id

            # Basic employee fields
            branch = emp.work_location_id.name or ''
            dept = emp.department_id.name or ''
            emp_no = emp.barcode or ''
            name = emp.name or ''
            designation = emp.job_id.name or ''

            gross_salary = contract.gross_salary_tti or 0.0
            # gross_salary = slip.line_ids.filtered(lambda x: x.name == 'Taxable Salary').total

            # Paid days (sum of WORK100 etc.)
            # paid_days = sum(slip.worked_days_line_ids.mapped('number_of_days'))
            paid_days = sum(
                slip.worked_days_line_ids
                .filtered(lambda w: w.code not in ['LEAVE90', 'OUT'])
                .mapped('number_of_days')
            )

            gross_for_month = slip.line_ids.filtered(lambda x: x.name == 'Taxable Salary').total

            # gross_for_month = (gross_salary / month_days) * paid_days if gross_salary else 0.0
            other_allowance = 0.0
            total_gross_payable = gross_for_month + other_allowance

            # Deductions
            def get_deduction(name_list):
                return sum(slip.line_ids.filtered(lambda l: l.name in name_list).mapped('total'))

            advance = get_deduction(["Advance Deduction"])
            loan = get_deduction(["Short Term Loan", "Car Loan", "Car loan"])
            # loan = sum(slip.line_ids.filtered(lambda l: l.name == "Loan Installment").mapped('total'))
            eobi = get_deduction(["EOBI"])
            mess = get_deduction(["Mess Deduction"])
            tax = get_deduction(["Tax Deduction"])
            other = get_deduction(["Other Deduction"])

            total_deduction = advance + loan + eobi + mess + tax + other
            net_pay = total_gross_payable - total_deduction

            values = [
                branch, dept, sr_no, emp_no, name, designation,
                gross_salary, paid_days, gross_for_month, other_allowance,
                total_gross_payable, advance, loan, eobi, mess, tax,
                other, total_deduction, net_pay
            ]

            for col, val in enumerate(values):
                if col == 2:
                    worksheet.write(row, col, val, center_format)
                elif isinstance(val, (int, float)):
                    worksheet.write_number(row, col, int(val), number_format)
                else:
                    worksheet.write(row, col, val, cell_format)

            sr_no += 1
            row += 1

        worksheet.set_column(0, len(headers) - 1, 18)

        workbook.close()
        output.seek(0)
        file_data = output.read()
        filename = 'salary_report.xlsx'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    # Generate Pdf report
    def action_generate_pdf(self):
        """Trigger PDF report"""
        self.ensure_one()
        return self.env.ref('visio_tti_salary_report.action_report_salary_pdf').report_action(self)
