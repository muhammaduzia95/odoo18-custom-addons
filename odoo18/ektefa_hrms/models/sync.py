
import requests
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class EktefaPayrollSync(models.Model):
    _name = 'ektefa.payroll.sync'
    _description = 'Ektefa Payroll Sync'
    _order = 'name DESC'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(EktefaPayrollSync, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(EktefaPayrollSync, self).write(vals)

    @api.model
    def action_sync_salaries_by_company(self):

        # Check if Ektefa integration is enabled
        integration_enabled = self.env.company.enable_ektefa_integration
        if not integration_enabled:
            _logger.info("Ektefa Integration is disabled.")
            return

        api_key = self.env.company.ektefa_api_key
        secret_key = self.env.company.ektefa_secret
        ektefa_company_id = self.env.company.ektefa_company_id

        print("data ", api_key , secret_key , ektefa_company_id )

        if not api_key or not secret_key and ektefa_company_id:
            raise UserError("Please configure Ektefa API credentials in Settings.")

        headers = {
            "x-apikey": api_key,
            "x-authorization": secret_key
        }
        params = {'company': ektefa_company_id}

        # Log the API request
        log_entry = self.env['ektefa.api.log'].create({
            'name': f"Salaries By CompanyID [{ektefa_company_id}] Sync",
            'request_data': str(params),  # Store the request body if needed
            'status': 'success',
        })

        # Step 1: Fetch all salaries by Ektefa CompanyID from the Ektefa API
        base_url = "https://appapi.ektefa.sa"
        employee_url = f"{base_url}/api/odoo/salaries"
        try:
            salaries_response = requests.get(url=employee_url, headers=headers, params=params)
            log_entry.response_data = salaries_response.text  # Store response data
            log_entry.response_timestamp = fields.Datetime.now()
            salaries_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("HTTP error while fetching employees: %s", e)
            return
        except requests.exceptions.ConnectionError as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Connection error while fetching employees: %s", e)
            return
        except requests.exceptions.Timeout as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Timeout error while fetching employees: %s", e)
            return
        except requests.exceptions.RequestException as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Error fetching employees from Ektefa API: %s", e)
            return

        salaries_data = salaries_response.json().get('result', {}).get('data', [])
        company_data = salaries_response.json().get('result', {}).get('company', {})
        if not salaries_data:
            log_entry.status = 'warning'
            log_entry.error_message = f"No salaries data by company id [{ektefa_company_id}] returned from Ektefa."
            _logger.warning(f"No salaries data by company id [{ektefa_company_id}] returned from Ektefa.")
            return

        # Step 2: Sync each salaries data into Odoo
        for salary in salaries_data:
            try:
                self._sync_payrun(salary, company_data)
            except Exception as e:
                _logger.error("Error syncing salaries %s: %s", salary.get('payrun', ''), e)
                self.env['mail.mail'].create({
                    'subject': 'Ektefa Sync Error',
                    'body_html': f'<p>Error syncing salary {salary.get("payrun", "")}: {str(e)}</p>',
                    'email_to': f'{self.env.user.email}',  # Change this to the appropriate recipient
                }).send()

        _logger.info(f"Successfully synced salaries  by company id [{ektefa_company_id}] from Ektefa.")

    def _sync_payrun(self, salary, company_data):
        payrun_id = salary['payrun']
        existing_salary = self.env['ektefa.payrun'].sudo().search([
            ('ektefa_payrun_id', '=', payrun_id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if existing_salary:
            return True

        debit_lines = []
        try:
            debit = salary.get('debit', {})
            for key, value in debit.items():
                debit_dict = {
                    'name': key,
                    'amount': value,
                }
                debit_lines.append((0, 0, debit_dict))
        except Exception as e:
            pass

        credit_lines = []
        try:
            credit = salary.get('credit', {})
            for key, value in credit.items():
                credit_dict = {
                    'name': key,
                    'amount': value,
                }
                credit_lines.append((0, 0, credit_dict))
        except Exception as e:
            pass

        salary_vals = {
            'ektefa_company_id': company_data['id'],
            'ektefa_company_name_en': company_data['name_en'],
            'ektefa_company_name_ar': company_data['name_ar'],
            'ektefa_company_cr_number': company_data['cr_number'],
            'name': f"Salary-{payrun_id}",
            'ektefa_payrun_id': payrun_id,
            'ektefa_month_date_text': salary['month'],
            'ektefa_debit_line_ids': debit_lines,
            'ektefa_credit_line_ids': credit_lines,
        }

        # Create 'ektefa.payrun' Record
        ektefa_payrun = self.env['ektefa.payrun'].create(salary_vals)
        if ektefa_payrun:
            ektefa_payrun_posted = ektefa_payrun.action_confirm()
            _logger.info("Salary synced for Payrun %s : %s.", payrun_id, ektefa_payrun.name)

    @api.model
    def action_sync_eos_by_company(self):

        # Check if Ektefa integration is enabled
        integration_enabled = self.env.company.enable_ektefa_integration
        if not integration_enabled:
            _logger.info("Ektefa Integration is disabled.")
            return

        api_key = self.env.company.ektefa_api_key
        secret_key = self.env.company.ektefa_secret
        ektefa_company_id = self.env.company.ektefa_company_id

        if not api_key or not secret_key and ektefa_company_id:
            raise UserError("Please configure Ektefa API credentials in Settings.")

        headers = {
            "x-apikey": api_key,
            "x-authorization": secret_key
        }
        params = {'company': ektefa_company_id}

        # Log the API request
        log_entry = self.env['ektefa.api.log'].create({
            'name': f"End of Services By CompanyID [{ektefa_company_id}] Sync",
            'request_data': str(params),  # Store the request body if needed
            'status': 'success',
        })

        # Step 1: Fetch all salaries by Ektefa CompanyID from the Ektefa API
        base_url = "https://appapi.ektefa.sa"
        employee_url = f"{base_url}/api/odoo/eos"
        try:
            eos_response = requests.get(url=employee_url, headers=headers, params=params)
            log_entry.response_data = eos_response.text  # Store response data
            log_entry.response_timestamp = fields.Datetime.now()
            eos_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("HTTP error while fetching employees: %s", e)
            return
        except requests.exceptions.ConnectionError as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Connection error while fetching employees: %s", e)
            return
        except requests.exceptions.Timeout as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Timeout error while fetching employees: %s", e)
            return
        except requests.exceptions.RequestException as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Error fetching employees from Ektefa API: %s", e)
            return

        eos_data = eos_response.json().get('result', {}).get('data', [])
        company_data = eos_response.json().get('result', {}).get('company', {})
        if not eos_data:
            log_entry.status = 'warning'
            log_entry.error_message = f"No End of Services data by company id [{ektefa_company_id}] returned from Ektefa."
            _logger.warning(f"No End of Services data by company id [{ektefa_company_id}] returned from Ektefa.")
            return

        # Step 2: Sync each salaries data into Odoo
        for eos in eos_data:
            try:
                self._sync_end_of_service(eos, company_data)
            except Exception as e:
                _logger.error("Error syncing End of Services  %s: %s", eos.get('eos_id', ''), e)
                self.env['mail.mail'].create({
                    'subject': 'Ektefa Sync Error',
                    'body_html': f'<p>Error syncing salary {eos.get("eos_id", "")}: {str(e)}</p>',
                    'email_to': f'{self.env.user.email}',  # Change this to the appropriate recipient
                }).send()

        _logger.info(f"Successfully synced end of services by company id [{ektefa_company_id}] from Ektefa.")

    def _sync_end_of_service(self, eos, company_data):
        eos_id = eos['eos_id']
        existing_salary = self.env['ektefa.end.of.service'].sudo().search([
            ('ektefa_eos_id', '=', eos_id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if existing_salary:
            return True

        debit_lines = []
        try:
            debit = eos.get('debit', {})
            for key, value in debit.items():
                debit_dict = {
                    'name': key,
                    'amount': value,
                }
                debit_lines.append((0, 0, debit_dict))
        except Exception as e:
            pass

        credit_lines = []
        try:
            credit = eos.get('credit', {})
            for key, value in credit.items():
                credit_dict = {
                    'name': key,
                    'amount': value,
                }
                credit_lines.append((0, 0, credit_dict))
        except Exception as e:
            pass

        salary_vals = {
            'ektefa_company_id': company_data['id'],
            'ektefa_company_name_en': company_data['name_en'],
            'ektefa_company_name_ar': company_data['name_ar'],
            'ektefa_company_cr_number': company_data['cr_number'],
            'name': f"EOS-{eos_id}",
            'ektefa_eos_id': eos_id,
            'ektefa_date_created_text': eos['date_created'],
            'ektefa_debit_line_ids': debit_lines,
            'ektefa_credit_line_ids': credit_lines,
        }

        # Create 'ektefa.end.of.service' Record
        ektefa_eos = self.env['ektefa.end.of.service'].create(salary_vals)
        if ektefa_eos:
            ektefa_eos_posted = ektefa_eos.action_confirm()
            _logger.info("Salary synced for End of Service %s : %s.", eos_id, ektefa_eos.name)

    @api.model
    def action_sync_loans_by_company(self):

        # Check if Ektefa integration is enabled
        integration_enabled = self.env.company.enable_ektefa_integration
        if not integration_enabled:
            _logger.info("Ektefa Integration is disabled.")
            return

        api_key = self.env.company.ektefa_api_key
        secret_key = self.env.company.ektefa_secret
        ektefa_company_id = self.env.company.ektefa_company_id

        if not api_key or not secret_key and ektefa_company_id:
            raise UserError("Please configure Ektefa API credentials in Settings.")

        headers = {
            "x-apikey": api_key,
            "x-authorization": secret_key
        }
        params = {'company': ektefa_company_id}

        # Log the API request
        log_entry = self.env['ektefa.api.log'].create({
            'name': f"Loans By CompanyID [{ektefa_company_id}] Sync",
            'request_data': str(params),  # Store the request body if needed
            'status': 'success',
        })

        # Step 1: Fetch all salaries by Ektefa CompanyID from the Ektefa API
        base_url = "https://appapi.ektefa.sa"
        employee_url = f"{base_url}/api/odoo/loans"
        try:
            loan_response = requests.get(url=employee_url, headers=headers, params=params)
            log_entry.response_data = loan_response.text  # Store response data
            log_entry.response_timestamp = fields.Datetime.now()
            loan_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("HTTP error while fetching loans: %s", e)
            return
        except requests.exceptions.ConnectionError as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Connection error while fetching loans: %s", e)
            return
        except requests.exceptions.Timeout as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Timeout error while fetching loans: %s", e)
            return
        except requests.exceptions.RequestException as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Error fetching loans from Ektefa API: %s", e)
            return

        loans_data = loan_response.json().get('result', {}).get('data', [])
        company_data = loan_response.json().get('result', {}).get('company', {})
        if not loans_data:
            log_entry.status = 'warning'
            log_entry.error_message = f"No Loans data by company id [{ektefa_company_id}] returned from Ektefa."
            _logger.warning(f"No Loans data by company id [{ektefa_company_id}] returned from Ektefa.")
            return

        # Step 2: Sync each salaries data into Odoo
        for loan in loans_data:
            try:
                self._sync_loan(loan, company_data)
            except Exception as e:
                _logger.error("Error syncing loan  %s: %s", loan.get('loan_id', ''), e)
                self.env['mail.mail'].create({
                    'subject': 'Ektefa Sync Error',
                    'body_html': f'<p>Error syncing salary {loan.get("loan_id", "")}: {str(e)}</p>',
                    'email_to': f'{self.env.user.email}',  # Change this to the appropriate recipient
                }).send()

        _logger.info(f"Successfully synced loans by company id [{ektefa_company_id}] from Ektefa.")

    def _sync_loan(self, loan, company_data):
        loan_id = loan.get('loan_id', False)

        existing_loan_id = self.env['ektefa.loans'].sudo().search([
            ('ektefa_loan_id', '=', loan_id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if existing_loan_id:
            return True

        partner_id = None
        ektefa_employee_id = loan.get('emp_id', False)
        if ektefa_employee_id:
            partner_id = self.env['res.partner'].sudo().search([
                ('ektefa_employee_id', '=', ektefa_employee_id),
            ], limit=1)

            partner_name = f"{loan.get('emp_en', False)} - {loan.get('emp_ar', False)}"
            if partner_id and partner_id.name != partner_name:
                partner_id.sudo().write({
                    'name': partner_name,
                })

            if not partner_id:
                partner_id = self.env['res.partner'].sudo().create({
                    'name': f"{loan.get('emp_en', False)} - {loan.get('emp_ar', False)}",
                    'ektefa_employee_id': ektefa_employee_id,
                })

        salary_vals = {
            'ektefa_company_id': company_data.get('id', False),
            'ektefa_company_name_en': company_data.get('name_en', False),
            'ektefa_company_name_ar': company_data.get('name_ar', False),
            'ektefa_company_cr_number': company_data.get('cr_number', False),
            'name': f"loan-{loan_id or ''}",
            'ektefa_loan_id': loan_id,
            'ektefa_comments': loan.get('comments', False),
            'ektefa_emp_id': loan.get('emp_id', False),
            'ektefa_emp_en': loan.get('emp_en', False),
            'ektefa_emp_ar': loan.get('emp_ar', False),
            'ektefa_payment_date_text': loan.get('payment_date', False),
            'ektefa_payment_method_id': loan.get('payment_method', {}).get('id', False),
            'ektefa_payment_method_name_en': loan.get('payment_method', {}).get('name_en', False),
            'ektefa_payment_method_name_ar': loan.get('payment_method', {}).get('name_ar', False),
            'ektefa_loan_amount': loan.get('amount', False),
            'partner_id': partner_id.id if partner_id is not None else False,
        }

        # Create 'ektefa.loans' Record
        ektefa_loan = self.env['ektefa.loans'].create(salary_vals)
        if ektefa_loan:
            ektefa_loan_posted = ektefa_loan.action_confirm()
            _logger.info("Loan synced for Ektefa %s : %s.", loan_id, ektefa_loan.name)


    @api.model
    def action_sync_loans_settlement_by_company(self):

        # Check if Ektefa integration is enabled
        integration_enabled = self.env.company.enable_ektefa_integration
        if not integration_enabled:
            _logger.info("Ektefa Integration is disabled.")
            return

        api_key = self.env.company.ektefa_api_key
        secret_key = self.env.company.ektefa_secret
        ektefa_company_id = self.env.company.ektefa_company_id

        if not api_key or not secret_key and ektefa_company_id:
            raise UserError("Please configure Ektefa API credentials in Settings.")

        headers = {
            "x-apikey": api_key,
            "x-authorization": secret_key
        }
        params = {'company': ektefa_company_id}

        # Log the API request
        log_entry = self.env['ektefa.api.log'].create({
            'name': f"Loans Settlement By CompanyID [{ektefa_company_id}] Sync",
            'request_data': str(params),  # Store the request body if needed
            'status': 'success',
        })

        # Step 1: Fetch all salaries by Ektefa CompanyID from the Ektefa API
        base_url = "https://appapi.ektefa.sa"
        employee_url = f"{base_url}/api/odoo/loans/settled"
        try:
            loan_settled_response = requests.get(url=employee_url, headers=headers, params=params)
            log_entry.response_data = loan_settled_response.text  # Store response data
            log_entry.response_timestamp = fields.Datetime.now()
            loan_settled_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("HTTP error while fetching loans settlement: %s", e)
            return
        except requests.exceptions.ConnectionError as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Connection error while fetching loans settlement: %s", e)
            return
        except requests.exceptions.Timeout as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Timeout error while fetching loans settlement: %s", e)
            return
        except requests.exceptions.RequestException as e:
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            _logger.error("Error fetching loans settlement from Ektefa API: %s", e)
            return

        loans_data = loan_settled_response.json().get('result', {}).get('data', [])
        company_data = loan_settled_response.json().get('result', {}).get('company', {})
        if not loans_data:
            log_entry.status = 'warning'
            log_entry.error_message = f"No Loans Settlement data by company id [{ektefa_company_id}] returned from Ektefa."
            _logger.warning(f"No Loans Settlement data by company id [{ektefa_company_id}] returned from Ektefa.")
            return

        # Step 2: Sync each salaries data into Odoo
        for loan in loans_data:
            try:
                self._sync_loan_settlement(loan, company_data)
            except Exception as e:
                _logger.error("Error syncing loan settlement %s: %s", loan.get('loan_id', ''), e)
                self.env['mail.mail'].create({
                    'subject': 'Ektefa Sync Error',
                    'body_html': f'<p>Error syncing salary {loan.get("loan_id", "")}: {str(e)}</p>',
                    'email_to': f'{self.env.user.email}',  # Change this to the appropriate recipient
                }).send()

        _logger.info(f"Successfully synced loans by company id [{ektefa_company_id}] from Ektefa.")

    def _sync_loan_settlement(self, loan, company_data):
        loan_id = loan.get('loan_id', False)

        existing_loan_id = self.env['ektefa.loans.settlement'].sudo().search([
            ('ektefa_loan_settlement_id', '=', loan_id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if existing_loan_id:
            return True

        partner_id = None
        ektefa_employee_id = loan.get('emp_id', False)
        if ektefa_employee_id:

            partner_id = self.env['res.partner'].sudo().search([
                ('ektefa_employee_id', '=', ektefa_employee_id),
            ], limit=1)
            partner_name = f"{loan.get('emp_en', False)} - {loan.get('emp_ar', False)}"

            if partner_id and partner_id.name != partner_name:
                partner_id.sudo().write({
                    'name': partner_name,
                })

            if not partner_id:
                partner_id = self.env['res.partner'].sudo().create({
                    'name': partner_name,
                    'ektefa_employee_id': ektefa_employee_id,
                })

        salary_vals = {
            'ektefa_company_id': company_data.get('id', False),
            'ektefa_company_name_en': company_data.get('name_en', False),
            'ektefa_company_name_ar': company_data.get('name_ar', False),
            'ektefa_company_cr_number': company_data.get('cr_number', False),
            'name': f"loan-settlement-{loan_id or ''}",
            'ektefa_loan_settlement_id': loan_id,
            'ektefa_comments': loan.get('comments', False),
            'ektefa_emp_id': loan.get('emp_id', False),
            'ektefa_emp_en': loan.get('emp_en', False),
            'ektefa_emp_ar': loan.get('emp_ar', False),
            'ektefa_settlement_date_text': loan.get('settlement_date', False),
            'ektefa_settlement_method_id': loan.get('settlement_method', {}).get('id', False),
            'ektefa_settlement_method_name_en': loan.get('settlement_method', {}).get('name_en', False),
            'ektefa_settlement_method_name_ar': loan.get('settlement_method', {}).get('name_ar', False),
            'ektefa_loan_settlement_amount': loan.get('amount', False),
            'partner_id': partner_id.id if partner_id is not None else False,
        }

        # Create 'ektefa.loans' Record
        ektefa_loan = self.env['ektefa.loans.settlement'].create(salary_vals)
        if ektefa_loan:
            ektefa_loan_posted = ektefa_loan.action_confirm()
            _logger.info("Loan synced for Ektefa %s : %s.", loan_id, ektefa_loan.name)


