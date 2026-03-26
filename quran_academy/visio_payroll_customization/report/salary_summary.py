from odoo import models, api, fields
from datetime import datetime, timedelta

class SalarySummary(models.AbstractModel):
    _name = "report.visio_payroll_customization.salary_summary_template"
    _description = "Salary Summary Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Fetches employee payslips for the selected month in the wizard.
        Computes first_child_dep dynamically and groups payslips accordingly.
        """
        month = fields.Date.from_string(data['month'])
        month_start = month.replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        # Fetch all payslips in "done" state for the selected month
        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', month_start),
            ('date_to', '<=', month_end),
            # ('state', '=', 'done')
        ])

        department_dict = {}

        for payslip in payslips:
            department = payslip.employee_id.department_id  # Employee's department

            # Compute first_child_dep using parent_path
            first_child_dep = False
            if department.parent_path:
                parent_ids = department.parent_path.split('/')
                if len(parent_ids) > 1 and parent_ids[1]:  # Ensure we have at least two levels
                    first_child_dep = self.env['hr.department'].browse(int(parent_ids[1]))

            if not first_child_dep:
                continue  # Skip if no first_child_dep is found

            # Initialize first_child_dep entry in dictionary
            if first_child_dep.id not in department_dict:
                department_dict[first_child_dep.id] = {
                    'name': first_child_dep.name,
                    'sub_departments': {},
                    'total_gross': 0,
                    'total_net': 0,
                    'total_deduction': 0,
                    'emp_eobi': 0,
                    'eobi_worker': 0,
                    'adv_salary': 0
                }

            # Fetch all child departments under first_child_dep
            child_departments = first_child_dep.child_ids
            for child_dep in child_departments:
                if child_dep.id not in department_dict[first_child_dep.id]['sub_departments']:
                    department_dict[first_child_dep.id]['sub_departments'][child_dep.id] = {
                        'name': child_dep.name,
                        'payslips': [],
                        'total_gross': 0,
                        'total_net': 0,
                        'total_deduction': 0,
                        'emp_eobi': 0,
                        'eobi_worker': 0,
                        'adv_salary': 0
                    }

            if department.id in department_dict[first_child_dep.id]['sub_departments']:
                sub_dept_data = department_dict[first_child_dep.id]['sub_departments'][department.id]
                sub_dept_data['payslips'].append(payslip)
                sub_dept_data['total_gross'] += payslip.gross_total
                sub_dept_data['total_net'] += payslip.net_payable
                sub_dept_data['total_deduction'] += payslip.total_deduction
                sub_dept_data['emp_eobi'] += payslip.emp_eobi
                sub_dept_data['eobi_worker'] += payslip.eobi_worker
                sub_dept_data['adv_salary'] += payslip.adv_salary

                # Update totals for first_child_dep
                department_dict[first_child_dep.id]['total_gross'] += payslip.gross_total
                department_dict[first_child_dep.id]['total_net'] += payslip.net_payable
                department_dict[first_child_dep.id]['total_deduction'] += payslip.total_deduction
                department_dict[first_child_dep.id]['emp_eobi'] += payslip.emp_eobi
                department_dict[first_child_dep.id]['eobi_worker'] += payslip.eobi_worker
                department_dict[first_child_dep.id]['adv_salary'] += payslip.adv_salary

        # **Remove sub-departments with zero total_gross and total_net**
        for first_child_id in list(department_dict.keys()):
            sub_departments = department_dict[first_child_id]['sub_departments']
            filtered_sub_departments = {
                sub_id: sub for sub_id, sub in sub_departments.items()
                if sub['total_gross'] > 0 or sub['total_net'] > 0 or sub['total_deduction'] > 0
                or sub['emp_eobi'] > 0 or sub['eobi_worker'] > 0 or sub['adv_salary'] > 0
            }

            # Replace with filtered sub_departments
            department_dict[first_child_id]['sub_departments'] = filtered_sub_departments

            # If all sub-departments were removed, remove the first_child_dep itself
            if not filtered_sub_departments:
                del department_dict[first_child_id]

        return {
            'doc_ids': payslips.ids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'month': month.strftime('%B %Y'),
            'departments': department_dict
        }