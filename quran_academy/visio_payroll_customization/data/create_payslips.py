import openpyxl
import logging
from odoo import api, models, fields
import datetime

_logger = logging.getLogger(__name__)


class HrPayslipImport(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def import_payslips_from_excel(self):
        """Import payslips from an Excel file efficiently."""
        # file_path = "custom_addons/quran_academy_addons/visio_payroll_customization/data/sheet_feb.xlsx"
        file_path = "/opt/odoo18/odoo18-custom-addons/visio_payroll_customization/data/sheet_feb.xlsx"

        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active

            headers = [cell.value.strip() if cell.value else "" for cell in sheet[1]]
            if "employee_sequence" not in headers or "date_from" not in headers:
                print("Error: The sheet must have 'employee_sequence' and 'date_from' columns.")
                _logger.info("Error: The sheet must have 'employee_sequence' and 'date_from' columns.")

                return

            emp_seq_idx = headers.index("employee_sequence")
            date_from_idx = headers.index("date_from")

            if "rate_per_month" not in headers:
                print("Error: The sheet must include a 'rate_per_month' column.")
                return

            field_indexes = {field: idx for idx, field in enumerate(headers)}

            # Fetch employees
            employees = self.env["hr.employee"].sudo().search([])
            _logger.info(f"Employees found: {len(employees)}")
            print(f"Employees found: {len(employees)}")
            employee_dict = {str(emp.employee_sequence): emp for emp in employees}

            # Fetch contracts along with their salary structures
            contracts = self.env["hr.contract"].sudo().search([])
            _logger.info(f"Contracts found: {len(contracts)}")
            print("Contracts found:", len(contracts))

            # Create a dictionary mapping employee_sequence to their contract
            contract_dict = {str(contract.employee_id.employee_sequence): contract for contract in contracts}

            payslip_records = []
            failed_records = 0  # Counter for failed inserts

            for row in sheet.iter_rows(min_row=2, values_only=True):
                employee_id = str(row[emp_seq_idx]).strip()

                if not employee_id or employee_id not in employee_dict:
                    _logger.info(f"Skipping row, employee not found: {employee_id}")
                    print(f"Skipping row, employee not found: {employee_id}")
                    continue

                # 🆕 Skip if `rate_per_month` is missing or None
                rate_idx = field_indexes.get("rate_per_month")
                if rate_idx is None or not row[rate_idx]:
                    print(f"Skipping row, 'rate_per_month' missing for employee {employee_id}")
                    continue

                # Get employee and contract
                employee = employee_dict[employee_id]
                contract = contract_dict.get(employee_id, None)  # Fetch contract if exists

                # Extract month and year from `date_from`
                date_from = row[date_from_idx]
                month_year = ""
                if isinstance(date_from, (str, datetime.date, datetime.datetime)):
                    date_from = fields.Date.to_date(date_from)  # Ensure it's a date object
                    month_year = date_from.strftime("%B-%Y")  # Format as "Month-Year"

                # Construct the name field
                payslip_name = f"Salary Slip of {employee.name} for {month_year}"

                payslip_values = {
                    "employee_id": employee.id,
                    "contract_id": contract.id if contract else False,
                    "struct_id": contract.struct_id.id if contract and contract.struct_id else False,
                    "name": payslip_name
                }

                # Map all remaining fields dynamically
                for field, idx in field_indexes.items():
                    if field in ["employee_sequence", "name"]:
                        continue  # Skip already handled fields

                    value = row[idx]
                    payslip_values[field] = value if value is not None else False

                try:
                    employee.write({"wage": payslip_values["rate_per_month"]})
                    employee.write({"loan_recovery": payslip_values["loan_recovery"]})
                    employee.write({"other_duty": payslip_values["other_duty"]})
                    contract.write({"loan_recovery": payslip_values["loan_recovery"]})
                    contract.write({"wage": payslip_values["rate_per_month"]})

                    payslip = self.env["hr.payslip"].sudo().create(payslip_values)
                    payslip_records.append(payslip.id)
                except Exception as e:
                    print(f"Failed to create payslip for employee {employee_id}: {e}")
                    _logger.info(f"Failed to create payslip for employee {employee_id}: {e}")
                    failed_records += 1

            print(f"Successfully imported {len(payslip_records)} payslips.")
            _logger.info(f"Successfully imported {len(payslip_records)} payslips.")
            if failed_records > 0:
                _logger.info(f"Failed to import {failed_records} payslips.")
                print(f"Failed to import {failed_records} payslips.")

        except Exception as e:
            _logger.info(f"Error processing Excel file: {e}")
            print(f"Error processing Excel file: {e}")
