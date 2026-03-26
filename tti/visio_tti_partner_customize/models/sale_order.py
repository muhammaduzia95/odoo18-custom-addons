# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.exceptions import ValidationError
import requests

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def action_confirm(self):
        for order in self:
            print("credit-test: [enter][action_confirm][order=%s][state=%s]" % (order.name, order.state))
            order._check_credit_limit_sale()
        res = super().action_confirm()
        print("credit-test: [exit][action_confirm][orders=%s]" % ",".join(self.mapped("name")))
        return res

    def action_confirm_now(self):
        for order in self:
            print("credit-test: [enter][action_confirm_now][order=%s][state=%s]" % (order.name, order.state))
            order._check_credit_limit_sale()
        res = super().action_confirm_now()
        print("credit-test: [exit][action_confirm_now][orders=%s]" % ",".join(self.mapped("name")))
        return res

    def action_quotation_done(self):
        for order in self:
            print("credit-test: [enter][action_quotation_done][order=%s][state=%s][skip-check]" % (order.name, order.state))
        res = super().action_quotation_done()
        print("credit-test: [exit][action_quotation_done][orders=%s]" % ",".join(self.mapped("name")))
        return res

    def action_quotation_approved(self):
        for order in self:
            print("credit-test: [enter][action_quotation_approved][order=%s][state=%s][skip-check]" % (order.name, order.state))
        res = super().action_quotation_approved()
        print("credit-test: [exit][action_quotation_approved][orders=%s]" % ",".join(self.mapped("name")))
        return res

    def create_invoice(self):
        print("credit-test: [enter][create_invoice][orders=%s]" % ",".join(self.mapped("name")))
        res = super().create_invoice()
        print("credit-test: [exit][create_invoice][orders=%s]" % ",".join(self.mapped("name")))
        return res


    def _check_credit_limit_sale(self):
        """
        Exposure = unpaid posted invoices (AR) +
                   pending-to-invoice on other confirmed SOs +
                   current order total
        -> block if exposure > partner.amount_credit_limit
        """
        self.ensure_one()
        order = self
        partner = order.partner_id.commercial_partner_id
        company = order.company_id
        limit = float(getattr(partner, 'amount_credit_limit', 0.0) or 0.0)

        print("credit-test: [check-start][order=%s][partner=%s][limit=%.2f][company=%s]" %
              (order.name, partner.display_name, limit, company.display_name))

        if limit <= 0.0:
            print("credit-test: [no-limit][skip][order=%s]" % order.name)
            return

        # 1) Unpaid posted receivables
        invs = self.env['account.move'].search([
            ('partner_id', 'child_of', partner.id),
            ('company_id', '=', company.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
        ])
        unpaid_posted = sum(invs.mapped('amount_residual'))
        print("credit-test: [step][unpaid_posted=%.2f][invoices_count=%d]" % (unpaid_posted, len(invs)))

        # 2) Pending-to-invoice on OTHER confirmed SOs
        other_sos = self.env['sale.order'].search([
            ('partner_id', 'child_of', partner.id),
            ('company_id', '=', company.id),
            ('state', 'in', ['sale', 'done', 'approved']),
            ('id', '!=', order.id),
        ])
        pending_other = sum(other_sos.mapped('amount_to_invoice'))
        print("credit-test: [step][pending_other_to_invoice=%.2f][other_so_count=%d]" % (pending_other, len(other_sos)))

        # 3) Current order total being committed now
        current_commit = float(order.amount_total or 0.0)
        print("credit-test: [step][current_order_total=%.2f]" % current_commit)

        projected = unpaid_posted + pending_other + current_commit
        print("credit-test: [exposure][unpaid_posted=%.2f][pending_other=%.2f][current=%.2f][projected=%.2f][limit=%.2f]" %
              (unpaid_posted, pending_other, current_commit, projected, limit))

        if projected > limit:
            print("credit-test: [BLOCK][order=%s][projected=%.2f][limit=%.2f]" %
                  (order.name, projected, limit))

            # Optional remote block call
            try:
                credit_flag = bool(getattr(partner, 'credit_check', False))
                code = getattr(partner, 'code', None)
                print("credit-test: [api-intent][credit_check=%s][code=%s]" % (credit_flag, code))
                if not credit_flag and code:
                    url = "http://202.59.76.150/api/blockcompany/%s/Y" % code
                    print("credit-test: [api-call][url=%s]" % url)
                    response = requests.patch(url)
                    response_body = "API Response: %s - %s" % (response.status_code, response.text)
                    print("credit-test: [api-response][%s]" % response_body)
                    partner.message_post(body=response_body)
                    order.message_post(body=response_body)
                    if response.status_code == 200:
                        partner.sudo().write({'credit_check': True})
            except Exception as e:
                print("credit-test: [api-error][%s]" % (e,))

            raise ValidationError(
                "Testing temporarily unavailable for this client. "
                "Please contact Credit Control for further information."
            )

        print("credit-test: [ALLOW][order=%s][projected=%.2f][limit=%.2f]" %
              (order.name, projected, limit))



# ---------------------------------------------------------------

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'

#     @api.model_create_multi
#     def create(self, vals_list):
#         record = super().create(vals_list)
#         for vals in vals_list:
#             record._check_credit_limit_sale()
#         return record

#     # def write(self, vals):
#     #     res = super().write(vals)
#     #     self._check_credit_limit_sale()
#     #     return res


#     def action_confirm_now(self):
#         res = super().action_confirm_now()
#         self._check_credit_limit_sale()
#         return res

#     def action_quotation_done(self):
#         res = super().action_quotation_done()
#         self._check_credit_limit_sale()
#         return res

#     def action_quotation_approved(self):
#         res = super().action_quotation_approved()
#         self._check_credit_limit_sale()
#         return res

#     def create_invoice(self):
#         res = super().action_quotation_approved()
#         self.create_invoice()
#         return res

#     def _check_credit_limit_sale(self):
#         for record in self:
#             if record.partner_id:
#                 total_sale_amount = sum(self.env['sale.order'].search([
#                     ('partner_id', '=', record.partner_id.id),
#                 ]).mapped('amount_total'))

#                 if record.partner_id.amount_credit_limit and total_sale_amount > record.partner_id.amount_credit_limit:
#                     if not record.partner_id.credit_check:
#                         code = record.partner_id.code
#                         try:
#                             url = f"http://202.59.76.150/api/blockcompany/{code}/Y"
#                             response = requests.patch(url)
#                             response_body = f"API Response: {response.status_code} - {response.text}"
#                             print(response_body)
#                             record.partner_id.message_post(
#                                 body=response_body
#                             )
#                             record.message_post(
#                                 body=response_body
#                             )
#                             if response.status_code == 200:
#                                 record.partner_id.sudo().write({'credit_check': True})
#                         except Exception as e:
#                             print(f"Error while calling API: {e}")

#                         raise ValidationError("Testing temporarily unavailable for this client. Please contact Credit Control for further information")
#                         # raise ValidationError(
#                             # f"Credit limit exceeded for {record.partner_id.name}!\n"
#                             # f"Total Sale Orders: {total_sale_amount}, "
#                             # f"Limit: {record.partner_id.amount_credit_limit}"
#                         # )
