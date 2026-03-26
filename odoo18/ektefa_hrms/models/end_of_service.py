
from odoo.exceptions import UserError
from odoo import models, fields, api
from datetime import datetime


class EktefaEndOfService(models.Model):
    _name = 'ektefa.end.of.service'
    _description = 'Ektefa End of Service'
    _order = 'id DESC'
    _check_company_auto = True


    # Company Details
    ektefa_company_id = fields.Char(string="Company ID")
    ektefa_company_name_en = fields.Char(string="Company Name EN")
    ektefa_company_name_ar = fields.Char(string="Company Name AR")
    ektefa_company_cr_number = fields.Char(string="Company CR Number")


    # End of Service Details
    name = fields.Char(string="Name")
    ektefa_eos_id = fields.Char(string="Ektefa EOS ID")

    ektefa_date_created = fields.Date(string="Created Date", compute="_compute_date_created", store=True,)
    ektefa_date_created_text = fields.Char(string="Created Date Text")

    ektefa_debit_line_ids = fields.One2many('ektefa.eos.debit.line', 'eos_id', string="Debit Lines")
    ektefa_credit_line_ids = fields.One2many('ektefa.eos.credit.line', 'eos_id', string="Credit Lines")

    # Status field for tracking the state of the EOS
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Canceled'),
    ], string="Status", default='draft')

    move_id = fields.Many2one('account.move', string='Journal Entry')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.depends('ektefa_date_created_text')
    def _compute_date_created(self):
        for eos in self:
            try:
                date_created = datetime.strptime(eos.ektefa_date_created_text, "%Y-%m-%d").date()
                eos.write({'ektefa_date_created':  date_created})
            except Exception as e:
                eos.ektefa_date_created = False

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

    def get_eos_debit_accounts(self, account_name=None):

        # EOS Net-Total Accounts
        # if account_name == 'net_total':
        credit = self.env.company.ektefa_eos_net_total_credit_account
        debit_1 = self.env.company.ektefa_eos_net_total_debit_account
        debit_2 = self.env.company.ektefa_eos_net_total_debit_account_2
        return credit or False, debit_1 or False, debit_2 or False

        # # EOS Deductions Accounts
        # elif account_name == 'deductions':
        #     credit = self.env.company.ektefa_eos_deductions_credit_account
        #     debit = self.env.company.ektefa_eos_deductions_debit_account
        #     return credit or False, debit or False

        return False, False, False

    def get_eos_credit_accounts(self, account_name):

        # # EOS Allowance Accounts
        # if account_name == 'allowance':
        #     credit = self.env.company.ektefa_eos_allowance_credit_account
        #     debit = self.env.company.ektefa_eos_allowance_debit_account
        #     return credit or False, debit or False

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


            # Prepare journal entries for ESO Debit Accounts
            # for line in slip.ektefa_debit_line_ids.filtered(lambda debit: debit.amount > 0):
            for line in slip.ektefa_debit_line_ids:
                allowance_credit_account_id, net_total_debit_account_id, deductions_debit_account_id  = slip.get_eos_debit_accounts()
                name = ""
                if line.name:
                    name = line.name
                line_name = f"EOS Net Total: {name.capitalize()}"
                # net_total_amount = round(abs(line.amount), 2)
                # debit_net_total_amount = round(net_total_amount/2, 2)
                # adjustment_amount = net_total_amount - (2 * debit_net_total_amount)  # Calculate adjustment for rounding

                if allowance_credit_account_id and net_total_debit_account_id and deductions_debit_account_id:
                    if line.name == 'net_total':
                        if line.amount >= 0:
                            move_lines.append((0, 0, {
                                'account_id': net_total_debit_account_id.id,
                                'name': line_name,
                                'debit': abs(line.amount),
                                'credit': 0,
                            }))
                        else:
                            move_lines.append((0, 0, {
                                'account_id': net_total_debit_account_id.id,
                                'name': line_name,
                                'debit': 0,
                                'credit': abs(line.amount),
                            }))
                    if line.name == 'deductions':
                        move_lines.append((0, 0, {
                            'account_id': deductions_debit_account_id.id,
                            'name': f"EOS Deductions: {name.capitalize()}",
                            'debit': abs(line.amount),
                            'credit': 0,
                        }))

            # Prepare journal entries for EOS Credit Accounts
            # for line in slip.ektefa_credit_line_ids.filtered(lambda credit: credit.amount > 0):
            for line in slip.ektefa_credit_line_ids:
                # credit_account_id, debit_account_id  = slip.get_eos_credit_accounts(line.name)
                allowance_credit_account_id, net_total_debit_account_id, deductions_debit_account_id  = slip.get_eos_debit_accounts()
                name = ""
                if line.name:
                    name = line.name
                line_name = f"EOS Allowance: {name.capitalize()}"
                if allowance_credit_account_id:
                    move_lines.append((0, 0, {
                        'account_id': allowance_credit_account_id.id,
                        'name': line_name,
                        'debit': 0,
                        'credit': abs(line.amount),
                    }))
            # print()
            # print('move_lines = ', move_lines)
            # print()
            # Create the journal entry
            move_vals = {
                'journal_id': self.env.company.ektefa_journal_id.id if self.env.company.ektefa_journal_id else False,
                'date': slip.ektefa_date_created,
                'ref': f"{slip.name} - ({slip.ektefa_date_created})",
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
        return super(EktefaEndOfService, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(EktefaEndOfService, self).write(vals)


class EktefaEOSDebitLine(models.Model):
    _name = 'ektefa.eos.debit.line'
    _description = 'Ektefa EOS Debit lines'
    _check_company_auto = True

    eos_id = fields.Many2one('ektefa.end.of.service', string="EOS", ondelete="cascade", required=True)
    name = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(EktefaEOSDebitLine, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(EktefaEOSDebitLine, self).write(vals)


class EktefaEOSCreditLine(models.Model):
    _name = 'ektefa.eos.credit.line'
    _description = 'Ektefa EOS Credit Line'

    eos_id = fields.Many2one('ektefa.end.of.service', string="EOS", ondelete="cascade", required=True)
    name = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(EktefaEOSCreditLine, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(EktefaEOSCreditLine, self).write(vals)
