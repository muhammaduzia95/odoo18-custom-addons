# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\eme_supplier_invoice_pdf.py
from odoo import models, api
from num2words import num2words


class EMESupplierInvoicePDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.supplier_invoice_pdf'
    _description = 'EME Supplier Invoice PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("\n==================== GENERATING SUPPLIER INVOICE ====================")
        print(f"DocIDs received: {docids}")

        invoice = self.env['account.move'].browse(docids).ensure_one()
        print(f"Invoice found: {invoice.name} (ID: {invoice.id})")

        company = invoice.company_id
        partner = invoice.partner_id

        # --- Fetch key data ---
        company_name = company.name or ""
        bill_no = invoice.name or ""
        bill_date = invoice.invoice_date or ""
        due_date = invoice.invoice_date_due or ""
        vendor_ref = invoice.ref or ""
        payment_terms = invoice.invoice_payment_term_id.name or ""

        vendor_name = partner.name or ""
        vendor_address = ", ".join(filter(None, [
            partner.street,
            partner.street2,
            partner.city,
            partner.country_id.code if partner.country_id else ""
        ]))
        vendor_trn = partner.vat or ""
        vendor_phone = partner.phone or ""
        vendor_email = partner.email or ""

        company_address = ", ".join(filter(None, [
            company.street,
            company.street2,
            company.city,
            company.country_id.code if company.country_id else ""
        ]))

        # --- Line Items ---
        line_data = []
        total_excl_vat_sum = 0.0
        total_vat_sum = 0.0
        total_incl_vat_sum = 0.0

        for index, line in enumerate(invoice.invoice_line_ids, start=1):
            vat_amount = 0.0
            vat_percent_display = "-"

            if line.tax_ids:
                taxes = line.tax_ids.compute_all(
                    price_unit=line.price_unit,
                    currency=invoice.currency_id,
                    quantity=line.quantity,
                )
                vat_amount = sum(t.get("amount", 0.0) for t in taxes.get("taxes", []))
                vat_percent_display = ", ".join(str(t.amount) for t in line.tax_ids)

            total_excl_vat = round(line.quantity * line.price_unit, 2)
            total_incl_vat = round(total_excl_vat + vat_amount, 2)
            vat_amount = round(vat_amount, 2)

            total_excl_vat_sum += total_excl_vat
            total_vat_sum += vat_amount
            total_incl_vat_sum += total_incl_vat

            line_data.append({
                "line_no": index,
                "default_code": line.product_id.default_code or "",
                "description": line.name or "",
                "qty": line.quantity or 0.0,
                "uom": line.product_uom_id.name or "",
                "rate": line.price_unit or 0.0,
                "total_excl_vat": total_excl_vat,
                "vat_percent_display": vat_percent_display,
                "vat_amount": vat_amount,
                "total_incl_vat": total_incl_vat,
            })

        totals = {
            "total_excl_vat_sum": round(total_excl_vat_sum, 2),
            "total_vat_sum": round(total_vat_sum, 2),
            "total_incl_vat_sum": round(total_incl_vat_sum, 2),
        }

        # Amount in words in Dirhams
        integer_part = int(round(totals["total_incl_vat_sum"] or 0))
        totals["amount_in_words"] = (
                num2words(integer_part, lang='en').title()
                + " Dirhams Only"
        )

        # Supplier Delivery Note Number
        supplier_dn_no = ""

        # Get Delivery (D.N.) from related Sale Order
        if invoice.invoice_origin:
            picking = self.env['stock.picking'].search([
                ('origin', '=', invoice.invoice_origin),
                ('picking_type_id.code', '=', 'outgoing'),
            ], limit=1, order="id desc")

            if picking:
                supplier_dn_no = picking.name

        # Add to dictionary
        po_number = invoice.customer_po_no or ""
        project_code = getattr(invoice, "project_name", "") or ""

        # Ship Date from related Sale Order
        ship_date = ""
        if invoice.invoice_origin:
            sale_order = self.env['sale.order'].search(
                [('name', '=', invoice.invoice_origin)],
                limit=1
            )
            if sale_order and sale_order.ship_date:
                ship_date = sale_order.ship_date.strftime('%d %b %Y')

        # Get Purchase Order linked to this Vendor Bill
        purchase_order = False
        if invoice.invoice_origin:
            purchase_order = self.env['purchase.order'].search(
                [('name', '=', invoice.invoice_origin)],
                limit=1
            )

        prepared_by = purchase_order.user_id if purchase_order else False

        salesperson = prepared_by.name if prepared_by else ""
        salesperson_dept = (
            prepared_by.employee_id.department_id.name
            if prepared_by and prepared_by.employee_id else ""
        )
        salesperson_desig = (
            prepared_by.employee_id.job_id.name
            if prepared_by and prepared_by.employee_id else ""
        )

        return {
            "doc_ids": invoice.ids,
            "doc_model": "account.move",
            "docs": invoice,

            "company": company,
            "company_name": company_name,

            # FIRST TABLE
            "si_no": bill_no,  # S.I No
            "bill_no": bill_no,  # (if needed elsewhere)
            "bill_date": bill_date,
            "due_date": due_date,
            "payment_terms": payment_terms,
            "si_date": bill_date,  # S.I Date = Invoice Date

            # Supplier Details (Vendor)
            "vendor_name": vendor_name,
            "vendor_address": vendor_address,
            "vendor_trn": vendor_trn,
            "vendor_phone": vendor_phone,
            "vendor_email": vendor_email,

            # SECOND TABLE VALUES
            "supplier_dn_no": supplier_dn_no,  # use the computed value
            "po_number": po_number,
            "project_code": project_code,

            # LINE ITEMS
            "line_data": line_data,
            "totals": totals,

            # Bill To (Vendor / Supplier)
            "customer_name": vendor_name,
            "customer_address": vendor_address,
            "customer_trn": vendor_trn,
            "customer_phone": vendor_phone,
            "customer_email": vendor_email,
            "project_name": getattr(invoice, "project_name", "") or "",

            # Ship To (Your Company / EME)
            "ship_to_address": company_address,
            "ship_date": ship_date,

            # Prepared By
            "salesperson": salesperson,
            "salesperson_dept": salesperson_dept,
            "salesperson_desig": salesperson_desig,

            "is_supplier_invoice": True,
        }
