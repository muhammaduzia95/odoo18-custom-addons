from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrLoan(models.Model):
    _inherit = 'hr.loan'

    account_move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True, copy=False)

    def action_approve(self):
        """ Approve loan or advance and create corresponding journal entry """
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))

            # Fetch config values
            config = self.env['ir.config_parameter'].sudo()
            if self.loan_type == 'short':
                journal_id = int(config.get_param('ohrms_loan.loan_journal_id') or 0)
                debit_account_id = int(config.get_param('ohrms_loan.loan_debit_account_id') or 0)
                credit_account_id = int(config.get_param('ohrms_loan.loan_credit_account_id') or 0)
            elif self.loan_type == 'car':
                journal_id = int(config.get_param('ohrms_loan.car_loan_journal_id') or 0)
                debit_account_id = int(config.get_param('ohrms_loan.car_loan_credit_account_id') or 0)
                credit_account_id = int(config.get_param('ohrms_loan.car_loan_debit_account_id') or 0)

            if data.type == 'advance':
                journal_id = int(config.get_param('ohrms_loan.adv_journal_id') or 0)
                debit_account_id = int(config.get_param('ohrms_loan.adv_debit_account_id') or 0)
                credit_account_id = int(config.get_param('ohrms_loan.adv_credit_account_id') or 0)

            if not journal_id or not debit_account_id or not credit_account_id:
                raise ValidationError(_("Configuration missing. Please check Loan & Advance settings."))

            # Match employee name with partner
            partner = self.env['res.partner'].search([('name', '=', data.employee_id.name)], limit=1)
            if not partner:
                raise ValidationError(_("No matching partner found for employee: %s") % data.employee_id.name)

            move_vals = {
                'date': data.date or fields.Date.today(),
                'journal_id': journal_id,
                'ref': f"{'Loan' if data.type == 'loan' else 'Advance'} - {data.name}",
                'partner_id': partner.id,
                'line_ids': [
                    (0, 0, {
                        'account_id': debit_account_id,
                        'name': f"{'Loan' if data.type == 'loan' else 'Advance'} for {data.employee_id.name}",
                        'debit': data.loan_amount,
                        'credit': 0.0,
                        'partner_id': partner.id,
                        # 'currency_id': data.currency_id.id,
                    }),
                    (0, 0, {
                        'account_id': credit_account_id,
                        'name': f"{'Loan' if data.type == 'loan' else 'Advance'} for {data.employee_id.name}",
                        'debit': 0.0,
                        'credit': data.loan_amount,
                        'partner_id': partner.id,
                        # 'currency_id': data.currency_id.id,
                    }),
                ]
            }

            move = self.env['account.move'].sudo().create(move_vals)
            move.action_post()

            data.account_move_id = move.id
            data.write({'state': 'approve'})