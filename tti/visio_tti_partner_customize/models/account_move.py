from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)
        # for vals in vals_list:
            # record._check_credit_limit_invoice()
        return record

    def write(self, vals):
        res = super().write(vals)
        # self._check_credit_limit_invoice()
        return res

    def _check_credit_limit_invoice(self):
        for record in self:
            if record.partner_id:
                total_invoice_amount = sum(self.env['account.move'].search([
                    ('partner_id', '=', record.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                ]).mapped('amount_total'))

                if record.partner_id.amount_credit_limit and total_invoice_amount > record.partner_id.amount_credit_limit:
                    if not record.partner_id.credit_check:
                        code = record.partner_id.code
                        try:
                            url = f"http://202.59.76.150/api/blockcompany/{code}/Y"
                            response = requests.patch(url)
                            response_body = f"API Response: {response.status_code} - {response.text}"
                            print(response_body)
                            record.partner_id.message_post(
                                body=response_body
                            )
                            record.message_post(
                                body=response_body
                            )
                            if response.status_code == 200:
                                record.partner_id.sudo().write({'credit_check': True})
                        except Exception as e:
                            print(f"Error while calling API: {e}")

                    raise ValidationError(
                        f"Credit limit exceeded for {record.partner_id.name}!\n"
                        f"Total invoices: {total_invoice_amount}, "
                        f"Limit: {record.partner_id.amount_credit_limit}"
                    )