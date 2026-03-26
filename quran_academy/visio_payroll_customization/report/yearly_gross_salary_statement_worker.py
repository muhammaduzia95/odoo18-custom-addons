# quran_academy\visio_payroll_customization\report\yearly_gross_salary_statement_worker.py
# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import io
import xlsxwriter
import calendar
from datetime import datetime, date as dt_date



class YearlyGrossSalaryStatementWorker(http.Controller):

    @http.route(
        '/yearly_gross_salary_statement_worker/export',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def export_yearly_gross_salary_worker(self, **kwargs):
        """Download an XLSX with static + dynamic‑date columns."""

        month_from = kwargs.get('month_from')
        month_to = kwargs.get('month_to')
        year = int(kwargs.get('year', datetime.today().year))

        payslip_domain = [('state', '=', 'done')]

        if month_from and month_to:
            # first day of from-month
            date_from = dt_date(year, int(month_from), 1)
            # last day of to-month
            last_day = calendar.monthrange(year, int(month_to))[1]
            date_to = dt_date(year, int(month_to), last_day)

            payslip_domain += [
                ('date_to', '>=', date_from),
                ('date_to', '<=', date_to)
            ]

        payslips = request.env['hr.payslip'].sudo().search(payslip_domain)

        if not payslips:
            return request.not_found(_(
                "No validated payslips found for the selection."))

        unique_dates = sorted({p.date_to for p in payslips})

        # "2/25/1931" style  – strip leading zeros
        def pretty(d):
            return f"{d.month}/{d.day}/{d.year}"

        date_headers = [pretty(d) for d in unique_dates]

        # Static headers
        static_headers = [
            'Category',  # first_child_dep  (hr.payslip)
            'Department',  # employee.department_id
            'WCode',  # employee.employee_sequence
            'Name',  # employee.name
            'Designation',  # employee.job_id
            'CNIC',  # employee.identification_id
        ]
        headers = static_headers + date_headers

        # (employee_id: { 'static': [..], 'amounts': {date: value} })
        rows = {}

        for slip in payslips:
            emp = slip.employee_id
            if emp.id not in rows:
                rows[emp.id] = {
                    'static': [
                        slip.first_child_dep or '',  # Category
                        emp.department_id.name or '',  # Department
                        emp.employee_sequence or '',  # WCode
                        emp.name,  # Name
                        emp.job_id.name or '',  # Designation
                        emp.identification_id or '',  # CNIC
                    ],
                    'amounts': {}  # date → gross
                }

            # find the gross salary in this payslip
            gross_line = slip.line_ids.filtered(lambda l: l.code == 'GROSS')
            gross_total = gross_line[0].total if gross_line else 0.0
            rows[emp.id]['amounts'][slip.date_to] = gross_total

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet('Gross Salary')

        # formats
        header_fmt = wb.add_format({'bold': True, 'bg_color': '#D9D9D9'})
        money_fmt = wb.add_format({'num_format': '#,##0.00'})

        # write header row
        for col, title in enumerate(headers):
            ws.write(0, col, title, header_fmt)

        # write data rows
        for row_idx, row_data in enumerate(rows.values(), start=1):
            # static cells
            for col_idx, value in enumerate(row_data['static']):
                ws.write(row_idx, col_idx, value)
            # dynamic salary cells
            for col_idx, date in enumerate(unique_dates, start=len(static_headers)):
                amount = row_data['amounts'].get(date, 0.0)
                ws.write_number(row_idx, col_idx, amount, money_fmt)

        # freeze header + first columns for usability
        ws.freeze_panes(1, len(static_headers))

        wb.close()
        output.seek(0)

        filename = f"Yearly Gross Salary Statement.xlsx"
        headers_http = [
            ('Content-Type',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', f'attachment; filename={filename}')
        ]
        return request.make_response(output.read(), headers=headers_http)
