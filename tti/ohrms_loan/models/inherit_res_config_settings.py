from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    loan_journal_id = fields.Many2one('account.journal', string="Loan Journal")
    loan_credit_account_id = fields.Many2one('account.account', string="Loan Credit Account")
    loan_debit_account_id = fields.Many2one('account.account', string="Loan Debit Account")

    adv_journal_id = fields.Many2one('account.journal', string="Advance Journal")
    adv_credit_account_id = fields.Many2one('account.account', string="Advance Credit Account")
    adv_debit_account_id = fields.Many2one('account.account', string="Advance Debit Account")

    car_loan_journal_id = fields.Many2one('account.journal', string="Car Loan Journal")
    car_loan_credit_account_id = fields.Many2one('account.account', string="Car Loan Credit Account")
    car_loan_debit_account_id = fields.Many2one('account.account', string="Car Loan Debit Account")

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('ohrms_loan.loan_journal_id', self.loan_journal_id.id or False)
        params.set_param('ohrms_loan.loan_credit_account_id', self.loan_credit_account_id.id or False)
        params.set_param('ohrms_loan.loan_debit_account_id', self.loan_debit_account_id.id or False)
        params.set_param('ohrms_loan.adv_journal_id', self.adv_journal_id.id or False)
        params.set_param('ohrms_loan.adv_credit_account_id', self.adv_credit_account_id.id or False)
        params.set_param('ohrms_loan.adv_debit_account_id', self.adv_debit_account_id.id or False)
        params.set_param('ohrms_loan.car_loan_journal_id', self.car_loan_journal_id.id or False)
        params.set_param('ohrms_loan.car_loan_credit_account_id', self.car_loan_credit_account_id.id or False)
        params.set_param('ohrms_loan.car_loan_debit_account_id', self.car_loan_debit_account_id.id or False)

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update({
            'loan_journal_id': self.env['account.journal'].browse(
                int(params.get_param('ohrms_loan.loan_journal_id') or 0)),
            'loan_credit_account_id': self.env['account.account'].browse(
                int(params.get_param('ohrms_loan.loan_credit_account_id') or 0)),
            'loan_debit_account_id': self.env['account.account'].browse(
                int(params.get_param('ohrms_loan.loan_debit_account_id') or 0)),
            'adv_journal_id': self.env['account.journal'].browse(
                int(params.get_param('ohrms_loan.adv_journal_id') or 0)),
            'adv_credit_account_id': self.env['account.account'].browse(
                int(params.get_param('ohrms_loan.adv_credit_account_id') or 0)),
            'adv_debit_account_id': self.env['account.account'].browse(
                int(params.get_param('ohrms_loan.adv_debit_account_id') or 0)),
            'car_loan_journal_id': self.env['account.journal'].browse(
                int(params.get_param('ohrms_loan.car_loan_journal_id') or 0)),
            'car_loan_credit_account_id': self.env['account.account'].browse(
                int(params.get_param('ohrms_loan.car_loan_credit_account_id') or 0)),
            'car_loan_debit_account_id': self.env['account.account'].browse(
                int(params.get_param('ohrms_loan.car_loan_debit_account_id') or 0)),
        })
        return res
