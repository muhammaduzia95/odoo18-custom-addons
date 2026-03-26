# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_payment_journal_report\report\payment_recovery_pdf.py
from odoo import models, api


class PaymentRecoveryPDF(models.AbstractModel):
    _name = 'report.visio_tti_payment_journal_report.payment_recovery_pdf'
    _description = 'Payment Recovery PDF Report'

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     wizard = self.env['payment.recovery.wizard'].browse(docids).ensure_one()
    #
    #     date_from = wizard.date_from
    #     date_to = wizard.date_to
    #
    #     payments = self.env['account.payment'].search([
    #         ('date', '>=', date_from),
    #         ('date', '<=', date_to),
    #     ], order="date asc")
    #
    #     # ============ BUILD CLEAN DICTIONARY ============
    #     def build_row(p):
    #         invoice = p.reconciled_invoice_ids[:1]
    #         residual = invoice.amount_residual if invoice else 0
    #         total = invoice.amount_total if invoice else 0
    #
    #         # --- COMMENT LOGIC ---
    #         if total and residual == 0:
    #             comment = "Recovered"
    #         elif total and 0 < residual < total:
    #             comment = "Partially"
    #         else:
    #             comment = ""
    #
    #         return {
    #             "id": p.move_id.name or "",
    #             "date": p.date.strftime('%d-%b-%Y') if p.date else "",
    #             "customer": p.partner_id.name or "",
    #             "instr_no": p.move_id.instr_no or "",
    #             "bill_no": p.move_id.bill_no or "",
    #             "amount": p.amount or 0.0,
    #             "sale_tax": p.sal_tax_wh or 0.0,
    #             "income_tax": p.income_tax_wh or 0.0,
    #             "total_amount": (p.amount or 0.0) + (p.sal_tax_wh or 0.0) + (p.income_tax_wh or 0.0),
    #             "comment": comment,
    #         }
    #
    #     # group into sections with clean rows
    #     sections = {
    #         "Cash": [build_row(p) for p in payments.filtered(lambda p: p.payment_category == "cash")],
    #         "Cheque": [build_row(p) for p in payments.filtered(lambda p: p.payment_category == "cheque")],
    #         "Online Transfer": [build_row(p) for p in payments.filtered(lambda p: p.payment_category == "online")],
    #     }
    #
    #     return {
    #         "doc_ids": [wizard.id],
    #         "doc_model": "payment.recovery.wizard",
    #         "docs": wizard,
    #         "wizard": wizard,
    #         "date_from": date_from,
    #         "date_to": date_to,
    #         "sections": sections,
    #     }

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['payment.recovery.wizard'].browse(docids).ensure_one()

        date_from = wizard.date_from
        date_to = wizard.date_to

        payments = self.env['account.payment'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ], order="date asc")

        def build_row(p):
            invoice = p.reconciled_invoice_ids[:1]
            residual = invoice.amount_residual if invoice else 0
            total = invoice.amount_total if invoice else 0

            # --- COMMENT LOGIC ---
            if total and residual == 0:
                comment = "Recovered"
            elif total and 0 < residual < total:
                comment = "Partially"
            else:
                comment = ""

            # --- TAX VISIBILITY LOGIC (same as Excel) ---
            sale_tax = p.sal_tax_wh or 0.0
            income_tax = p.income_tax_wh or 0.0

            sale_acc = getattr(p, 'sale_wh_tax_account', False)
            income_acc = getattr(p, 'income_wh_tax_account', False)

            if not sale_acc or sale_acc.tti_report_type in ('default', False, ''):
                sale_tax = 0.0

            if not income_acc or income_acc.tti_report_type in ('default', False, ''):
                income_tax = 0.0

            total_amount = (p.amount or 0.0) + sale_tax + income_tax

            return {
                "id": p.move_id.name or "",
                "date": p.date.strftime('%d-%b-%Y') if p.date else "",
                "customer": p.partner_id.name or "",
                "instr_no": p.move_id.instr_no or "",
                "bill_no": p.move_id.bill_no or "",
                "amount": p.amount or 0.0,
                "sale_tax": sale_tax,
                "income_tax": income_tax,
                "total_amount": total_amount,
                "comment": comment,
            }

        section_defs = [
            ("Cash", "cash"),
            ("Cheque", "cheque"),
            ("Online Transfer", "online"),
        ]

        sections = []
        grand_totals = {
            "amount": 0.0,
            "sale_tax": 0.0,
            "income_tax": 0.0,
            "total_amount": 0.0,
        }

        for title, category in section_defs:
            section_payments = payments.filtered(lambda p: p.payment_category == category)
            if not section_payments:
                continue

            rows = [build_row(p) for p in section_payments]

            subtotal = {
                "amount": sum(r["amount"] for r in rows),
                "sale_tax": sum(r["sale_tax"] for r in rows),
                "income_tax": sum(r["income_tax"] for r in rows),
                "total_amount": sum(r["total_amount"] for r in rows),
            }

            # accumulate grand totals
            for key in grand_totals:
                grand_totals[key] += subtotal[key]

            sections.append({
                "title": title,
                "rows": rows,
                "subtotal": subtotal,
                "is_last": False,  # will set later
            })

        # mark last section (if any) so we can show Grand Total under it
        if sections:
            sections[-1]["is_last"] = True

        return {
            "doc_ids": [wizard.id],
            "doc_model": "payment.recovery.wizard",
            "docs": wizard,
            "wizard": wizard,
            "date_from": date_from,
            "date_to": date_to,
            "sections": sections,
            "grand_totals": grand_totals,
        }
