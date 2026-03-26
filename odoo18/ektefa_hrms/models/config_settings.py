
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ########################################################################################
    # Ektefa API Details
    ########################################################################################

    ektefa_api_key = fields.Char(
        related='company_id.ektefa_api_key',
        readonly=False,
    )
    ektefa_secret = fields.Char(
        related='company_id.ektefa_secret',
        readonly=False,
    )
    enable_ektefa_integration = fields.Boolean(
        related='company_id.enable_ektefa_integration',
        readonly=False,
    )
    enable_ektefa_journal_posts = fields.Boolean(
        related='company_id.enable_ektefa_journal_posts',
        readonly=False,
    )
    ektefa_company_id = fields.Integer(
        related='company_id.ektefa_company_id',
        readonly=False,
    )

    ########################################################################################
    # Ektefa Journal
    ########################################################################################

    ektefa_journal_id = fields.Many2one(
        comodel_name='account.journal',
        related='company_id.ektefa_journal_id',
        readonly=False,
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
        related="company_id.ektefa_salaries_basic_accommodation_credit_account",
        readonly=False,
    )
    ektefa_salaries_basic_accommodation_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_salaries_basic_accommodation_debit_account",
        readonly=False,
    )

    # Allowances Accounts
    ektefa_allowances_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_allowances_credit_account",
        readonly=False,
    )
    ektefa_allowances_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_allowances_debit_account",
        readonly=False,
    )

    # Additions Accounts
    ektefa_additions_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_additions_credit_account",
        readonly=False,
    )
    ektefa_additions_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_additions_debit_account",
        readonly=False,
    )

    ########################################################################################
    # Ektefa Payrun Credit Accounts
    ########################################################################################

    # Deductions Accounts
    ektefa_deductions_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_deductions_credit_account",
        readonly=False,
    )
    ektefa_deductions_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_deductions_debit_account",
        readonly=False,
    )

    # Deductions Gosi Accounts
    ektefa_deductions_gosi_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_deductions_gosi_credit_account",
        readonly=False,
    )
    ektefa_deductions_gosi_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_deductions_gosi_debit_account",
        readonly=False,
    )

    ########################################################################################
    # Ektefa End of Service Debit Accounts
    ########################################################################################

    # EOS Deductions Accounts
    ektefa_eos_deductions_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_eos_deductions_credit_account",
        readonly=False,
    )
    ektefa_eos_deductions_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_eos_deductions_debit_account",
        readonly=False,
    )

    # EOS Net-Total Accounts
    ektefa_eos_net_total_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_eos_net_total_credit_account",
        readonly=False,
    )
    ektefa_eos_net_total_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_eos_net_total_debit_account",
        readonly=False,
    )
    ektefa_eos_net_total_debit_account_2 = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_eos_net_total_debit_account_2",
        readonly=False,
    )

    ########################################################################################
    # Ektefa End of Service Credit Accounts
    ########################################################################################

    # EOS Allowance Accounts
    ektefa_eos_allowance_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_eos_allowance_credit_account",
        readonly=False,
    )
    ektefa_eos_allowance_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_eos_allowance_debit_account",
        readonly=False,
    )

    ########################################################################################
    # Ektefa Loans Accounts
    ########################################################################################

    # Loans Accounts
    ektefa_loans_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_loans_credit_account",
        readonly=False,
    )
    ektefa_loans_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_loans_debit_account",
        readonly=False,
    )

    ########################################################################################
    # Ektefa Loans Settlement Accounts
    ########################################################################################

    # Loans Settlement Accounts
    ektefa_loans_settlement_credit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_loans_settlement_credit_account",
        readonly=False,
    )
    ektefa_loans_settlement_debit_account = fields.Many2one(
        comodel_name="account.account",
        related="company_id.ektefa_loans_settlement_debit_account",
        readonly=False,
    )

