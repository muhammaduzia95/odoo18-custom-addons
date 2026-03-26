from odoo import models, api
from num2words import num2words


class TaxDebitNotePDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.tax_debit_note_pdf'
    _description = 'EME Tax Debit Note PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("\n==================== GENERATING EME Tax Credit Note ====================")
        print(f"DocIDs received: {docids}")

        invoice = self.env['account.move'].browse(docids).ensure_one()
        print(f"Invoice found: {invoice.name} (ID: {invoice.id})")

        company = invoice.company_id
        partner = invoice.partner_id

        # --- Fetch key data ---
        company_name = company.name or ""
        salesperson = invoice.invoice_user_id.name or ""
        salesperson_desig = invoice.invoice_user_id.employee_id.job_id.name or ""
        salesperson_dept = invoice.invoice_user_id.employee_id.department_id.name or ""
        po_number = invoice.customer_po_no or ""
        po_date = invoice.customer_po_date or ""
        pi_date = invoice.invoice_date or ""
        due_date = invoice.invoice_date_due or ""
        payment_terms = invoice.invoice_payment_term_id.name or ""
        terms_n_conditions = invoice.narration or ""
        pcode = ""
        grn_no = ""
        delivery_note_no = ""
        ship_date = ""
        if invoice.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
            if sale_order:
                picking = self.env['stock.picking'].search([('origin', '=', sale_order.name)], limit=1)
                ship_date = sale_order.ship_date
                if picking:
                    delivery_note_no = picking.name

        print(f"Salesperson: {salesperson}")
        print(f"PI Date: {pi_date}")
        print(f"Due Date: {due_date}")
        print(f"Payment Terms: {payment_terms}")

        # --- Bill To (Customer) Details ---
        customer_name = partner.name or ""
        customer_address = ", ".join(filter(None, [
            partner.street,
            partner.street2,
            partner.city,
            partner.country_id and partner.country_id.code or ""
        ]))
        project_name = getattr(invoice, "project_name", "") or ""
        customer_trn = partner.vat or ""
        customer_phone = partner.phone or ""
        customer_email = partner.email or ""

        # --- Ship To Details ---
        ship_to_address = invoice.partner_shipping_id.contact_address or ""
        # ship_date = (
        #         invoice.invoice_origin and
        #         invoice.invoice_line_ids.mapped("sale_line_ids.order_id.picking_ids")
        #         .filtered(lambda p: p.state == "done")
        #         .sorted(key=lambda p: p.date_done)[-1]
        #         .date_done or ""
        # ) if invoice.invoice_line_ids else ""

        # --- Line Items ---
        line_data = []
        total_excl_vat_sum = 0.0
        total_vat_sum = 0.0
        total_incl_vat_sum = 0.0

        for index, line in enumerate(invoice.invoice_line_ids, start=1):
            vat_amount = 0.0
            vat_percent_total = 0.0
            vat_percent_display = "-"

            # --- Taxes Calculation ---
            if line.tax_ids:
                taxes_computed = line.tax_ids.compute_all(
                    line.price_unit,
                    currency=line.move_id.currency_id,
                    quantity=line.quantity,
                    product=line.product_id,
                    partner=line.move_id.partner_id
                )

                # VAT Amount (sum of all taxes)
                vat_amount = sum(t.get("amount", 0.0) for t in taxes_computed.get("taxes", []))

                # Display all tax rates (e.g., "5, 20")
                vat_percent_display = ", ".join(str(t.amount) for t in line.tax_ids)

                # Total tax percent (sum of all rates)
                vat_percent_total = sum(line.tax_ids.mapped("amount"))

            # --- Totals per line ---
            total_excl_vat = line.quantity * line.price_unit
            total_with_vat = total_excl_vat + vat_amount

            # --- Round Values ---
            vat_amount = round(vat_amount, 2)
            total_excl_vat = round(total_excl_vat, 2)
            total_with_vat = round(total_with_vat, 2)

            # --- Category & Subcategory ---
            category = ""
            subcategory = ""
            if line.product_id.categ_id:
                category_rec = line.product_id.categ_id
                category = category_rec.parent_id.name or ""
                subcategory = category_rec.name or ""

            # --- Accumulate Totals ---
            total_excl_vat_sum += total_excl_vat
            total_vat_sum += vat_amount
            total_incl_vat_sum += total_with_vat

            # --- Append row data ---
            line_data.append({
                "line_no": index,
                "default_code": line.product_id.default_code or "-",
                "description": line.name or "",
                "brand": getattr(line.product_id.product_tmpl_id, "x_studio_brand", "") or "",
                "uom": line.product_uom_id.name or "",
                "qty": line.quantity or 0.0,
                "rate": line.price_unit or 0.0,
                "vat_percent_display": vat_percent_display,  # e.g. "5, 20"
                "vat_percent_total": vat_percent_total,  # sum of tax %
                "vat_amount": vat_amount,
                "total_excl_vat": total_excl_vat,
                "total_incl_vat": total_with_vat,
                "category": category,
                "subcategory": subcategory,
            })

        # --- Totals for summary rows ---
        totals = {
            "total_excl_vat_sum": round(total_excl_vat_sum, 2),
            "total_vat_sum": round(total_vat_sum, 2),
            "total_incl_vat_sum": round(total_incl_vat_sum, 2),
        }

        # Amount in words in Dirhams
        integer_part = int(round(total_incl_vat_sum or 0))
        totals["amount_in_words"] = (
                num2words(integer_part, lang='en').title()
                + " Dirhams Only"
        )

        return {
            "doc_ids": invoice.ids,
            "doc_model": "account.move",
            "docs": invoice,
            "company": company,
            "partner": partner,
            "company_name": company_name,

            # Static Info
            "salesperson": salesperson,
            "po_number": po_number,
            "po_date": po_date,
            "pi_date": pi_date,
            "due_date": due_date,
            "pcode": pcode,
            "grn_no": grn_no,
            "payment_terms": payment_terms,
            "delivery_note_no": delivery_note_no,

            # Bill To
            "customer_name": customer_name,
            "customer_address": customer_address,
            "project_name": project_name,
            "customer_trn": customer_trn,
            "customer_phone": customer_phone,
            "customer_email": customer_email,

            # Ship To
            "ship_to_address": ship_to_address,
            "ship_date": ship_date,

            # Invoice Lines
            'line_data': line_data,
            'totals': totals,

            "salesperson_dept": salesperson_dept,
            "salesperson_desig": salesperson_desig,

            # Terms & Conditions
            "terms_n_conditions": terms_n_conditions

        }
