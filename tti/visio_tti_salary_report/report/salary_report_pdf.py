# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_salary_report\report\salary_report_pdf.py
from odoo import models, api
from collections import defaultdict
import calendar

import logging
_logger = logging.getLogger(__name__)
class SalaryReportPDF(models.AbstractModel):
    _name = 'report.visio_tti_salary_report.report_salary_pdf_template'
    _description = 'Salary Report PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tti.salary.report.wizard'].browse(docids)
        wizard = docs[:1]  # single wizard
        if not wizard:
            print(">>> No wizard docs found")
            return {"doc_ids": docids, "doc_model": "tti.salary.report.wizard", "docs": docs, "lines": [], "groups": []}

        w = wizard[0]
        month_days = calendar.monthrange(w.date_from.year, w.date_from.month)[1]
        print(">>> Wizard dates:", w.date_from, w.date_to, "month_days:", month_days)

        month_label = w.date_from.strftime('%B %Y') if w.date_from else ''

        lines = []
        sr_no = 1

        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', w.date_from),
            ('date_to', '<=', w.date_to),
            ('state', '=', 'done'),
        ])
        print(">>> Found payslips:", payslips.ids)

        def get_deduction(slip, name_list):
            return sum(slip.line_ids.filtered(lambda l: l.name in name_list).mapped('total'))

        for slip in payslips:
            emp = slip.employee_id
            contract = slip.contract_id

            branch = (getattr(emp, 'work_location_id', False) and emp.work_location_id.name) or (
                        getattr(emp, 'work_location', False) or '')
            dept = emp.department_id.name or ''
            emp_no = emp.barcode or ''
            name = emp.name or ''
            designation = emp.job_id.name or ''
            gross_salary = contract.gross_salary_tti or 0.0
            # gross_salary = slip.paid_amount or 0.0

            # gross_salary = slip.line_ids.filtered(lambda x: x.name == 'Taxable Salary').total
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

            advance = get_deduction(slip, ["Advance Deduction"])
            loan = get_deduction(slip, ["Short Term Loan", "Car Loan", "Car loan"])
            #loan = sum(slip.line_ids.filtered(lambda l: l.name == "Loan Installment").mapped('total'))
            eobi = get_deduction(slip, ["EOBI"])
            mess = get_deduction(slip, ["Mess Deduction"])
            tax = get_deduction(slip, ["Tax Deduction"])
            other = get_deduction(slip, ["Other Deduction"])

            total_deduction = advance + loan + eobi + mess + tax + other
            net_pay = total_gross_payable - total_deduction
            logging.info("--------------------Total payable:", net_pay)

            row = {
                "branch": branch,
                "department": dept,
                "sr": sr_no,
                "emp_no": emp_no,
                "name": name,
                "designation": designation,
                "gross_salary": gross_salary,
                "paid_days": paid_days,
                "gross_for_month": gross_for_month,
                "other_allowance": other_allowance,
                "total_gross": total_gross_payable,
                "advance": advance,
                "loan": loan,
                "eobi": eobi,
                "mess": mess,
                "tax": tax,
                "other": other,
                "total_deduction": total_deduction,
                "net_pay": net_pay,
                "month_label": month_label,

            }
            logging.info("-------------------Row:", row)
            print(">>> Row:", row)
            lines.append(row)
            sr_no += 1

        # group in python
        by_branch = defaultdict(lambda: defaultdict(list))
        for l in lines:
            by_branch[l.get('branch') or '—'][l.get('department') or '—'].append(l)

        # groups = []
        # for branch, deptmap in by_branch.items():
        #     departments = []
        #     for dept, rows in deptmap.items():
        #         # sort rows by Emp.No (string or number)
        #         sorted_rows = sorted(rows, key=lambda r: r['emp_no'] or '')
        #         # reassign Sr.No inside this department
        #         for i, r in enumerate(sorted_rows, start=1):
        #             r['sr'] = i
        #         departments.append({'department': dept, 'rows': sorted_rows})
        #
        #     groups.append({'branch': branch, 'departments': departments})

        groups = []
        for branch, deptmap in by_branch.items():
            departments = []
            for dept in sorted(deptmap.keys()):  # A, B, C...
                rows = deptmap[dept]
                sorted_rows = sorted(rows, key=lambda r: r['emp_no'] or '')
                for i, r in enumerate(sorted_rows, start=1):
                    r['sr'] = i
                departments.append({'department': dept, 'rows': sorted_rows})

            groups.append({'branch': branch, 'departments': departments})

        print(">>> Groups:", groups)
        logging.info("--------------------Groups:", groups)
        return {
            "doc_ids": docs.ids,
            "doc_model": "tti.salary.report.wizard",
            "docs": docs,
            "lines": lines,
            "groups": groups,
            "month_label": month_label,

        }
