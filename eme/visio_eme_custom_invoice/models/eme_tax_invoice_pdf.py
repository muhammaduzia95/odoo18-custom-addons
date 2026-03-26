# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\eme_tax_invoice_pdf.py
from odoo import models, api
from num2words import num2words


class EMETaxInvoiceServicePDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.eme_tax_invoice_service_pdf'
    _description = 'EME Tax Invoice (Service) PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("\n==================== GENERATING EME TAX INVOICE (SERVICE) ====================")
        print(f"DocIDs received: {docids}")

        invoice = self.env['account.move'].browse(docids).ensure_one()
        print(f"Invoice found: {invoice.name} (ID: {invoice.id})")

        company = invoice.company_id
        partner = invoice.partner_id

        # --- Fetch key data ---
        po_number = invoice.customer_po_no or ""
        po_date = invoice.customer_po_date or ""
        pi_date = invoice.invoice_date or ""
        invoice_date = invoice.invoice_date or ""
        due_date = invoice.invoice_date_due or ""
        payment_terms = invoice.invoice_payment_term_id.name or ""
        delivery_note_no = ""
        if invoice.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
            if sale_order:
                picking = self.env['stock.picking'].search([('origin', '=', sale_order.name)], limit=1)
                if picking:
                    delivery_note_no = picking.name


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
        ship_to_address = customer_address
        ship_date = ""

        # --- Line Items ---
        line_data = []
        for line in invoice.invoice_line_ids:
            # VAT percent (sum of tax amounts)
            vat_percent = sum(line.tax_ids.mapped("amount")) if line.tax_ids else 0.0

            # Total excluding VAT
            total_excl_vat = line.price_subtotal or 0.0

            # VAT Amount
            vat_amount = total_excl_vat * vat_percent / 100

            # Total including VAT
            total_incl_vat = total_excl_vat + vat_amount

            line_data.append({
                "line_no": len(line_data) + 1,
                "default_code": line.product_id.default_code or "",
                "description": line.name or "",
                "brand": getattr(line.product_id.product_tmpl_id, "x_studio_brand", "") or "",
                "qty": line.quantity or 0.0,
                "uom": line.product_uom_id.name or "",
                "rate": line.price_unit or 0.0,
                "total_excl_vat": total_excl_vat,
                "vat_percent_display": f"{vat_percent}%" if vat_percent else "-",
                "vat_amount": vat_amount,
                "total_incl_vat": total_incl_vat,
            })

        # --- Totals ---
        total_excl_vat_sum = sum(l["total_excl_vat"] for l in line_data)
        total_vat_sum = sum(l["vat_amount"] for l in line_data)
        total_incl_vat_sum = sum(l["total_incl_vat"] for l in line_data)

        # Amount in words based on Total (Incl. VAT)
        integer_part = int(round(total_incl_vat_sum or 0))
        amount_in_words = (
                num2words(integer_part, lang='en').title()
                + " Dirhams Only"
        )

        # ------------------------------------------
        # Salesperson Info (from Sale Order)
        # ------------------------------------------
        salesperson = ""
        salesperson_dept = ""
        salesperson_desig = ""

        sale_order = None
        if invoice.invoice_origin:
            sale_order = self.env['sale.order'].search(
                [('name', '=', invoice.invoice_origin)],
                limit=1
            )

        if sale_order and sale_order.user_id:
            user = sale_order.user_id
            employee = user.employee_id

            salesperson = user.name or ""
            salesperson_dept = employee.department_id.name if employee else ""
            salesperson_desig = employee.job_id.name if employee else ""

        return {
            "doc_ids": invoice.ids,
            "doc_model": "account.move",
            "docs": invoice,
            "company": company,
            "partner": partner,

            # Static Info
            "salesperson": salesperson,
            "salesperson_dept": salesperson_dept,
            "salesperson_desig": salesperson_desig,
            "po_number": po_number,
            "po_date": po_date,
            "pi_date": pi_date,
            "invoice_date": invoice_date,
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

            # Ship To (optional)
            "ship_to_address": ship_to_address,
            "ship_date": ship_date,

            # Invoice Lines
            "line_data": line_data,

            # Totals (IMPORTANT FIX)
            "totals": {
                "total_excl_vat_sum": total_excl_vat_sum,
                "total_vat_sum": total_vat_sum,
                "total_incl_vat_sum": total_incl_vat_sum,
                "amount_in_words": amount_in_words,
            },
        }
