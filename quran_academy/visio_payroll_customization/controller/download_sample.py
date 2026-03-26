from odoo import http
from odoo.http import request
import io
import xlsxwriter
from datetime import datetime, timedelta

class FileDownloadController(http.Controller):

    @http.route('/download/excel/file/<string:month>', type='http', auth='user')
    def download_sample_file(self, month=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        headers = [
            # Basic Salary Tab
            'Worker Code',
            'Employee Name',
            'Designation',
            'Rate Per Month',
            'Other Duty',
            'Comments',

            # Allowances Tab
            'Medical',
            'Ext-Arrears-Night',
            'Daily Wages',
            'Special Allowance',
            'Other Deduction',


            'Leave in cash',
            'Over Time',
            'Without Pay',
            'Attendance Star',
            'One Time Deduction',

            # Deductions Tab
            'Loan Recovery',
            'Advance Salary',
            'Income Tax',
            'Provident Fund',
            'Mess Bill',
            'House Rent',
            'Vehicle Charges',
            'Electricity/Gas Bill',
            'EOBI Worker',
            'EOBI Employer',
            'Arrear EOBI Employer',
            'Arrear EOBI Worker',

            'EOBI',
            'Leave Encash 2/3',
            'Paid By',
        ]

        for col_num in range(len(headers)):
            worksheet.set_column(col_num, col_num, 25)

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # payslip = request.env['hr.payslip'].sudo().search([], limit=1, order="id desc")
        # if payslip:
        #     month = payslip.date_to.replace(day=1)
        # else:
        #     month = datetime.today().replace(day=1)
        # selected_month_start = month.replace(day=1)
        # next_month = month.replace(day=28) + timedelta(days=4)
        # selected_month_end = next_month.replace(day=1) - timedelta(days=1)

        file_name = f'Sample of ({month}) Payslips'
        month = datetime.strptime(month, '%Y-%m-%d')
        selected_month_start = month.replace(day=1)
        next_month = month.replace(day=28) + timedelta(days=4)
        selected_month_end = next_month.replace(day=1) - timedelta(days=1)

        payslips = request.env['hr.payslip'].sudo().search([
            ('date_from', '>=', selected_month_start),
            ('date_to', '<=', selected_month_end),
            ('state', '=', 'draft'),
            '|',
            ('employee_id.date_leaving', '=', False),
            ('employee_id.date_leaving', '>=', selected_month_end),
        ])
        # employee_ids = payslips.mapped('employee_id')
        # employee_domain = [('active', '=', True)]
        # if employee_ids:
        #     employee_domain += [('id', 'in', employee_ids.ids)]
        # employees = request.env['hr.employee'].sudo().search(employee_domain)

        row = 1
        for payslip in payslips:
            worksheet.write(row, 0, payslip.worker_code or '')  # Worker Code
            worksheet.write(row, 1, payslip.employee_id.name or '')  # Employee Name
            worksheet.write(row, 2, payslip.employee_job_title or '')
            worksheet.write(row, 3, payslip.rate_per_month or 0.00)
            worksheet.write(row, 4, payslip.other_duty or 0.00)
            worksheet.write(row, 5, payslip.comments or '')

            worksheet.write(row, 6, payslip.medical or 0.00)
            worksheet.write(row, 7, payslip.ext_arrear_night or 0.00)
            worksheet.write(row, 8, payslip.daily_wages or 0.00)
            worksheet.write(row, 9, payslip.special_allowance_qa or 0.00)
            worksheet.write(row, 10, payslip.other_deduction or 0.00)

            worksheet.write(row, 11, payslip.leave_in_cash or 0.00)
            worksheet.write(row, 12, payslip.over_time or 0.00)
            worksheet.write(row, 13, payslip.wo_pay or 0.00)
            worksheet.write(row, 14, payslip.attendance_star or 0.00)
            worksheet.write(row, 15, payslip.one_time_deduction or 0.00)

            worksheet.write(row, 16, payslip.loan_recovery or 0.00)
            worksheet.write(row, 17, payslip.adv_salary or 0.00)
            worksheet.write(row, 18, payslip.income_tax or 0.00)
            worksheet.write(row, 19, payslip.prov_fund or 0.00)
            worksheet.write(row, 20, payslip.tel_bill or 0.00)
            worksheet.write(row, 21, payslip.h_rent or 0.00)
            worksheet.write(row, 22, payslip.veh_charges or 0.00)
            worksheet.write(row, 23, payslip.elec_gas_bill or 0.00)
            worksheet.write(row, 24, payslip.eobi_worker or 0.00)
            worksheet.write(row, 25, payslip.emp_eobi or 0.00)
            worksheet.write(row, 26, payslip.eobi_emp_diff or 0.00)
            worksheet.write(row, 27, payslip.eobi_worker_diff or 0.00)
            worksheet.write(row, 28, payslip.eobi)
            worksheet.write(row, 29, payslip.leave_encash)
            worksheet.write(row, 30, payslip.paid_by or '')

            row += 1

        workbook.close()

        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{file_name}.xlsx"')
            ]
        )
