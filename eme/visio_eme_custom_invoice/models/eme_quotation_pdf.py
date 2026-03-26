# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\eme_quotation_pdf.py
from odoo import models, api
from num2words import num2words


class EMEQuotationPDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.eme_quotation_pdf'
    _description = 'EME Quotation PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("\n==================== GENERATING EME PROFORMA SERVICE INVOICE ====================")
        print(f"DocIDs received: {docids}")

        order = self.env['sale.order'].browse(docids).ensure_one()
        print(f"Quotation found: {order.name} (ID: {order.id})")

        company = order.company_id
        partner = order.partner_id

        # --- Fetch key data ---
        company_name = company.name or ""
        salesperson = order.user_id.name or ""
        salesperson_desig = order.user_id.employee_id.job_id.name or ""
        salesperson_dept = order.user_id.employee_id.department_id.name or ""

        # If you have custom PO fields on sale.order, map them here, otherwise keep blank:
        po_number = getattr(order, "customer_po_no", "") or ""
        po_date = getattr(order, "customer_po_date", "") or ""

        # Quotation date / validity / payment terms
        pi_date = order.date_order or ""  # you can rename label in XML from P.I Date -> Quotation Date
        due_date = order.validity_date or ""  # optional; can be blank if not used
        payment_terms = order.payment_term_id.name or ""
        terms_n_conditions = order.note or ""  # quotation terms/note

        delivery_note_no = ""  # quotations usually have no DN

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
        project_name = (order.opportunity_id.name if order.opportunity_id else "")
        customer_trn = partner.vat or ""
        customer_phone = partner.phone or ""
        customer_email = partner.email or ""

        # --- Other Info (Quotation) ---
        attention_name = order.attention_id.name or ""
        consultant_name = order.consultant_id.name or ""
        subject = order.subject or ""
        details = order.details or ""

        # --- Ship To Details ---
        ship_to_address = order.partner_shipping_id.contact_address or ""
        ship_date = getattr(order, "ship_date", "") or ""


        # --- Line Items ---
        line_data = []
        total_excl_vat_sum = 0.0
        total_vat_sum = 0.0
        total_incl_vat_sum = 0.0

        for index, line in enumerate(order.order_line.filtered(lambda l: not l.display_type), start=1):
            vat_amount = 0.0
            vat_percent_total = 0.0
            vat_percent_display = "-"

            # --- Taxes Calculation ---
            if line.tax_id:
                vat_percent_display = ", ".join(str(t.amount) for t in line.tax_id)
                vat_percent_total = sum(line.tax_id.mapped("amount"))

            # VAT amount from line totals (most reliable for SO lines)
            vat_amount = (line.price_total - line.price_subtotal)

            # --- Totals per line ---
            total_excl_vat = line.price_subtotal
            total_with_vat = line.price_total

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
                "uom": line.product_uom.name or "",
                "qty": line.product_uom_qty or 0.0,
                "rate": line.price_unit or 0.0,
                "vat_percent_display": vat_percent_display,  # e.g. "5, 20"
                "vat_percent_total": vat_percent_total,  # sum of tax %
                "vat_amount": vat_amount,
                "total_excl_vat": total_excl_vat,
                "total_incl_vat": total_with_vat,
                "category": category,
                "subcategory": subcategory,
            })

        # --- Discount ---
        discount_sum = 0.0
        for line in order.order_line.filtered(lambda l: not l.display_type):
            # discount on each line = qty * unit_price * discount%
            discount_sum += (line.product_uom_qty * line.price_unit) * (line.discount / 100.0)

        discount_sum = round(discount_sum, 2)

        # --- Totals for summary rows ---
        totals = {
            "total_excl_vat_sum": round(order.amount_untaxed, 2),
            "discount_sum": discount_sum,
            "total_vat_sum": round(order.amount_tax, 2),
            "total_incl_vat_sum": round(order.amount_total, 2),
        }

        tax_rates = sorted({
            t.amount
            for ln in order.order_line.filtered(lambda l: not l.display_type)
            for t in ln.tax_id
            if t.amount_type == 'percent'
        })
        totals["vat_percent_display"] = ", ".join(f"{r:g}%" for r in tax_rates) if tax_rates else "0%"

        # Amount in words in Dirhams
        integer_part = int(round(totals["total_incl_vat_sum"] or 0))
        totals["amount_in_words"] = (
                num2words(integer_part, lang='en').title()
                + " Dirhams Only"
        )

        return {
            "doc_ids": order.ids,
            "doc_model": "sale.order",
            "docs": order,
            "company": company,
            "partner": partner,
            "company_name": company_name,

            # Static Info
            "salesperson": salesperson,
            "po_number": po_number,
            "po_date": po_date,
            "pi_date": pi_date,
            "due_date": due_date,
            "payment_terms": payment_terms,
            "delivery_note_no": delivery_note_no,

            # Bill To
            "customer_name": customer_name,
            "customer_address": customer_address,
            "project_name": project_name,
            "customer_trn": customer_trn,
            "customer_phone": customer_phone,
            "customer_email": customer_email,

            # Other Info
            "attention_name": attention_name,
            "consultant_name": consultant_name,
            "subject": subject,
            "details": details,

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
