
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    ########################################################################################
    # Ektefa API Details
    ########################################################################################

    enable_ektefa_integration = fields.Boolean(
        string="Enable Ektefa Integration",
    )
    ektefa_api_key = fields.Char(
        string="Ektefa API Key",
    )
    ektefa_secret = fields.Char(
        string="Ektefa Authorization Secret",
    )
    ektefa_company_id = fields.Integer(
        string="Ektefa Company ID",
    )
    enable_ektefa_journal_posts = fields.Boolean(
        string="Enable Auto Journal Posts",
    )

    ########################################################################################
    # Ektefa Journal
    ########################################################################################

    ektefa_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Ektefa Journal",
        domain="[('type', '=', 'general')]",
        help='The accounting journal where automatic ektefa payroll will be registered'
    )

    ########################################################################################
    # Ektefa Payrun Debit Accounts
    ########################################################################################

    # Salaries Basic Accommodation Accounts
    ektefa_salaries_basic_accommodation_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Salaries Basic Accommodation Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_salaries_basic_accommodation_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Salaries Basic Accommodation Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    # Allowances Accounts
    ektefa_allowances_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Allowances Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_allowances_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Allowances Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    # Additions Accounts
    ektefa_additions_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Additions Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_additions_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Additions Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    ########################################################################################
    # Ektefa Payrun Credit Accounts
    ########################################################################################

    # Deductions Accounts
    ektefa_deductions_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Deductions Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_deductions_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Deductions Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    # Deductions Gosi Accounts
    ektefa_deductions_gosi_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Deductions Gosi Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_deductions_gosi_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Deductions Gosi Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    ########################################################################################
    # Ektefa End of Service Debit Accounts
    ########################################################################################

    # EOS Deductions Accounts
    ektefa_eos_deductions_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa EOS Deductions Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_eos_deductions_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa EOS Deductions Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    # EOS Net-Total Accounts
    ektefa_eos_net_total_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa EOS Net-Total Allowance Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_eos_net_total_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa EOS Net-Total Debit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_eos_net_total_debit_account_2 = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa EOS Net-Total Deductions Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    ########################################################################################
    # Ektefa End of Service Credit Accounts
    ########################################################################################

    # EOS Allowance Accounts
    ektefa_eos_allowance_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa EOS Allowance Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_eos_allowance_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa EOS Allowance Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    ########################################################################################
    # Ektefa Loans Accounts
    ########################################################################################

    # Loans Accounts
    ektefa_loans_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Loans Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_loans_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Loans Debit Account",
        domain="[('deprecated', '=', False)]"
    )

    ########################################################################################
    # Ektefa Loans Settlement Accounts
    ########################################################################################

    # Loans Settlement Accounts
    ektefa_loans_settlement_credit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Loans Settlement Credit Account",
        domain="[('deprecated', '=', False)]"
    )
    ektefa_loans_settlement_debit_account = fields.Many2one(
        comodel_name="account.account",
        string="Ektefa Loans Settlement Debit Account",
        domain="[('deprecated', '=', False)]"
    )
