
from odoo.exceptions import UserError
from odoo import models, fields, api
from datetime import datetime


class EktefaLoans(models.Model):
    _name = 'ektefa.loans'
    _description = 'Ektefa Loans'
    _order = 'id DESC'
    _check_company_auto = True


    # Company Details
    ektefa_company_id = fields.Char(string="Company ID")
    ektefa_company_name_en = fields.Char(string="Company Name EN")
    ektefa_company_name_ar = fields.Char(string="Company Name AR")
    ektefa_company_cr_number = fields.Char(string="Company CR Number")


    # End of Service Details
    name = fields.Char(string="Name")
    ektefa_loan_id = fields.Char(string="Ektefa Loan ID")
    ektefa_loan_amount = fields.Float(string="Loan Amount")
    ektefa_comments = fields.Char(string="Comments")

    ektefa_emp_id = fields.Char(string="Employee ID")
    ektefa_emp_en = fields.Char(string="Employee Name EN")
    ektefa_emp_ar = fields.Char(string="Employee Name AR")


    ektefa_payment_method_id = fields.Char(string="Payment Method ID")
    ektefa_payment_method_name_en = fields.Char(string="Name EN")
    ektefa_payment_method_name_ar = fields.Char(string="Name AR")

    ektefa_payment_date = fields.Date(string="Payment Date", compute="_compute_payment_date", store=True,)
    ektefa_payment_date_text = fields.Char(string="Payment Date Text")

    # Status field for tracking the state of the EOS
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Canceled'),
    ], string="Status", default='draft')

    move_id = fields.Many2one('account.move', string='Journal Entry')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Partner')

    @api.depends('ektefa_payment_date_text')
    def _compute_payment_date(self):
        for loan in self:
            try:
                payment_date = datetime.strptime(loan.ektefa_payment_date_text, "%Y-%m-%d").date()
                loan.write({'ektefa_payment_date':  payment_date})
            except Exception as e:
                loan.ektefa_payment_date = False

    def button_cancel(self):
        self.ensure_one()
        for salary in self:
            if salary.move_id:
                salary.move_id.button_cancel()
                salary.state = 'cancel'

    def button_draft(self):
        self.ensure_one()
        for salary in self:
            if salary.move_id:
                salary.move_id.button_draft()
            salary.state = 'draft'

    def get_eos_debit_accounts(self, account_name):

        # EOS Deductions Accounts
        if account_name == 'deductions':
            credit = self.env.company.ektefa_eos_deductions_credit_account
            debit = self.env.company.ektefa_eos_deductions_debit_account
            return credit or False, debit or False

        # EOS Net-Total Accounts
        elif account_name == 'net_total':
            credit = self.env.company.ektefa_eos_net_total_credit_account
            debit = self.env.company.ektefa_eos_net_total_debit_account
            return credit or False, debit or False

        return False, False

    def get_eos_credit_accounts(self, account_name):

        # EOS Allowance Accounts
        if account_name == 'allowance':
            credit = self.env.company.ektefa_eos_allowance_credit_account
            debit = self.env.company.ektefa_eos_allowance_debit_account
            return credit or False, debit or False

        return False, False

    def action_confirm(self):
        """Confirm the loan slip and create the journal entries."""
        for slip in self:

            if slip.move_id:
                if slip.move_id.state == 'draft':
                    slip.move_id.action_post()
                    slip.state = 'posted'
                continue

            if slip.state != 'draft':
                raise UserError("Only draft salary slips can be posted.")

            move_lines = []

            # Create the journal entry for the payment method
            credit_account_id = self.env.company.ektefa_loans_credit_account
            debit_account_id = self.env.company.ektefa_loans_debit_account

            name = ""
            if slip.ektefa_payment_method_name_en or slip.ektefa_payment_method_name_ar:
                name = slip.ektefa_payment_method_name_en or slip.ektefa_payment_method_name_ar
            line_name = f"Payment Method: {name}, Comments: {self.ektefa_comments}"
            if credit_account_id and debit_account_id:
                move_lines.append((0, 0, {
                    'account_id': credit_account_id.id,
                    'name': line_name,
                    'debit': 0,
                    'credit': abs(slip.ektefa_loan_amount),
                    'partner_id': self.partner_id.id if self.partner_id else False,
                }))
                move_lines.append((0, 0, {
                    'account_id': debit_account_id.id,
                    'name': line_name,
                    'debit': abs(slip.ektefa_loan_amount),
                    'credit': 0,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                }))

            # Create the journal entry
            move_vals = {
                'journal_id': self.env.company.ektefa_journal_id.id if self.env.company.ektefa_journal_id else False,
                'date': slip.ektefa_payment_date,
                'ref': f"{slip.name} - ({slip.ektefa_payment_date})",
                'line_ids': move_lines,
                'move_type': 'entry',
                'ektefa_employee_id': slip.ektefa_emp_id,
                'ektefa_employee_name': f"{slip.ektefa_emp_en} - {slip.ektefa_emp_ar}",
            }
            move = self.env['account.move'].create(move_vals)
            if move:
                slip.move_id = move.id
                if self.env.company.enable_ektefa_journal_posts:
                    move_posted = move.action_post()
                    slip.state = 'posted'

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(EktefaLoans, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(EktefaLoans, self).write(vals)
