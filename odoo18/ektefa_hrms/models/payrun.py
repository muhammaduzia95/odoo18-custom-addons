
from odoo.exceptions import UserError
from odoo import models, fields, api
from datetime import datetime


class EktefaPayRun(models.Model):
    _name = 'ektefa.payrun'
    _description = 'Ektefa Payrun'
    _order = 'id DESC'
    _check_company_auto = True


    # Company Details
    ektefa_company_id = fields.Char(string="Company ID")
    ektefa_company_name_en = fields.Char(string="Company Name EN")
    ektefa_company_name_ar = fields.Char(string="Company Name AR")
    ektefa_company_cr_number = fields.Char(string="Company CR Number")


    # Payrun Details
    name = fields.Char(string="Name")
    ektefa_payrun_id = fields.Char(string="Ektefa Payrun ID")

    ektefa_month_date = fields.Date(string="Month Date", compute="_compute_month_date", store=True,)
    ektefa_month_date_text = fields.Char(string="Month Date Text")

    ektefa_debit_line_ids = fields.One2many('ektefa.payrun.debit.line', 'payrun_id', string="Debit Lines")
    ektefa_credit_line_ids = fields.One2many('ektefa.payrun.credit.line', 'payrun_id', string="Credit Lines")

    # Status field for tracking the state of the Payrun
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Canceled'),
    ], string="Status", default='draft')

    move_id = fields.Many2one('account.move', string='Journal Entry')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.depends('ektefa_month_date_text')
    def _compute_month_date(self):
        for payrun in self:
            try:
                month_date = datetime.strptime(payrun.ektefa_month_date_text, "%Y-%m-%d").date()
                payrun.write({'ektefa_month_date':  month_date})
            except Exception as e:
                payrun.ektefa_month_date = False

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

    def get_payrun_debit_accounts(self, account_name):

        # Salaries Basic Accommodation Accounts
        if account_name == 'salaries_basic_accomodation':
            credit = self.env.company.ektefa_salaries_basic_accommodation_credit_account
            debit = self.env.company.ektefa_salaries_basic_accommodation_debit_account
            return credit or False, debit or False

        # Allowances Accounts
        elif account_name == 'allowances':
            credit = self.env.company.ektefa_allowances_credit_account
            debit = self.env.company.ektefa_allowances_debit_account
            return credit or False, debit or False

        # Additions Accounts
        elif account_name == 'additions':
            credit = self.env.company.ektefa_additions_credit_account
            debit = self.env.company.ektefa_additions_debit_account
            return credit or False, debit or False

        return False, False

    def get_payrun_credit_accounts(self, account_name):

        # Deductions Accounts
        if account_name == 'deductions':
            credit = self.env.company.ektefa_deductions_credit_account
            debit = self.env.company.ektefa_deductions_debit_account
            return credit or False, debit or False

        # Deductions Gosi Accounts
        elif account_name == 'deductions_gosi':
            credit = self.env.company.ektefa_deductions_gosi_credit_account
            debit = self.env.company.ektefa_deductions_gosi_debit_account
            return credit or False, debit or False

        return False, False

    def action_confirm(self):
        """Confirm the salary slip and create the journal entries."""
        for slip in self:

            if slip.move_id:
                if slip.move_id.state == 'draft':
                    slip.move_id.action_post()
                    slip.state = 'posted'
                continue

            if slip.state != 'draft':
                raise UserError("Only draft salary slips can be posted.")

            move_lines = []


            # Prepare journal entries for Payrun Debit Accounts
            # for line in slip.ektefa_debit_line_ids.filtered(lambda line: line.amount > 0):
            for line in slip.ektefa_debit_line_ids:
                credit_account_id, debit_account_id  = slip.get_payrun_debit_accounts(line.name)
                name = ""
                if line.name:
                    name = line.name
                line_name = f"Payrun Debit: {name.capitalize()}"
                if credit_account_id and debit_account_id:
                    move_lines.append((0, 0, {
                        'account_id': credit_account_id.id,
                        'name': line_name,
                        'debit': 0,
                        'credit': abs(line.amount),
                    }))
                    move_lines.append((0, 0, {
                        'account_id': debit_account_id.id,
                        'name': line_name,
                        'debit': abs(line.amount),
                        'credit': 0,
                    }))

            # Prepare journal entries for Payrun Credit Accounts
            # for line in slip.ektefa_credit_line_ids.filtered(lambda line: line.amount > 0):
            for line in slip.ektefa_credit_line_ids:
                credit_account_id, debit_account_id  = slip.get_payrun_credit_accounts(line.name)
                name = ""
                if line.name:
                    name = line.name
                line_name = f"Payrun Credit: {name.capitalize()}"
                if credit_account_id and debit_account_id:
                    move_lines.append((0, 0, {
                        'account_id': credit_account_id.id,
                        'name': line_name,
                        'debit': 0,
                        'credit': abs(line.amount),
                    }))
                    move_lines.append((0, 0, {
                        'account_id': debit_account_id.id,
                        'name': line_name,
                        'debit': abs(line.amount),
                        'credit': 0,
                    }))

            # Create the journal entry
            move_vals = {
                'journal_id': self.env.company.ektefa_journal_id.id if self.env.company.ektefa_journal_id else False,
                'date': slip.ektefa_month_date,
                'ref': f"{slip.name} - ({slip.ektefa_month_date})",
                'line_ids': move_lines,
                'move_type': 'entry',
            }
            move = self.env['account.move'].create(move_vals)
            if move:
                slip.move_id = move.id
                if self.env.company.enable_ektefa_journal_posts:
                    move_posted =  move.action_post()
                    slip.state = 'posted'

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(EktefaPayRun, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(EktefaPayRun, self).write(vals)


class EktefaPayrunDebitLine(models.Model):
    _name = 'ektefa.payrun.debit.line'
    _description = 'Ektefa Payrun Debit lines'
    _check_company_auto = True

    payrun_id = fields.Many2one('ektefa.payrun', string="Payrun", ondelete="cascade", required=True)
    name = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(EktefaPayrunDebitLine, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(EktefaPayrunDebitLine, self).write(vals)


class EktefaPayrunCreditLine(models.Model):
    _name = 'ektefa.payrun.credit.line'
    _description = 'Ektefa Payrun Credit Line'

    payrun_id = fields.Many2one('ektefa.payrun', string="Payrun", ondelete="cascade", required=True)
    name = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(EktefaPayrunCreditLine, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(EktefaPayrunCreditLine, self).write(vals)