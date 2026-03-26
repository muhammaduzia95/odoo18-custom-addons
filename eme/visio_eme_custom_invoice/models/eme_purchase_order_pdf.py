# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\eme_purchase_order_pdf.py

from odoo import models, api
from num2words import num2words


class EMEPurchaseOrderPDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.purchase_order_pdf'
    _description = 'EME Purchase Order PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(f"[PO PDF] DocIDs received: {docids}")

        po = self.env['purchase.order'].browse(docids).ensure_one()

        company = po.company_id
        vendor = po.partner_id

        # === Basic PO Info ===
        po_number = po.name or ""
        po_date = po.date_order or ""
        buyer = po.user_id.name or ""
        buyer_dept = po.user_id.employee_id.department_id.name or ""
        buyer_desig = po.user_id.employee_id.job_id.name or ""

        # === Vendor Info ===
        vendor_name = vendor.name or ""
        vendor_address = ", ".join(filter(None, [
            vendor.street,
            vendor.street2,
            vendor.city,
            vendor.country_id.code if vendor.country_id else ""
        ]))
        vendor_trn = vendor.vat or ""
        vendor_phone = vendor.phone or ""
        vendor_email = vendor.email or ""

        # === Delivery Info ===
        place_of_delivery = po.x_studio_place_of_delivery if hasattr(po, "x_studio_place_of_delivery") else ""

        # Ship Date (from purchase.order field: ship_date)
        ship_date = ""
        if getattr(po, "ship_date", False):
            ship_date = po.ship_date.strftime("%d %b %Y")

        # === PO Line Items ===
        line_data = []

        for index, line in enumerate(po.order_line, start=1):
            vat_percent = sum(line.taxes_id.mapped("amount")) if line.taxes_id else 0
            vat_amount = (line.price_subtotal * vat_percent) / 100
            total_incl_vat = line.price_subtotal + vat_amount

            line_data.append({
                "line_no": index,
                "default_code": line.product_id.default_code or "-",
                "description": line.name or "",
                "brand": line.product_id.product_tmpl_id.x_studio_brand if hasattr(line.product_id.product_tmpl_id,
                                                                                   "x_studio_brand") else "",
                "uom": line.product_uom.name or "",
                "qty": line.product_qty or 0,
                "rate": line.price_unit or 0,
                "total_excl_vat": line.price_subtotal or 0,
                "vat_percent_display": f"{vat_percent}%",
                "vat_amount": vat_amount,
                "total_incl_vat": total_incl_vat,
            })

        # === Totals ===
        amount_untaxed = po.amount_untaxed or 0
        amount_tax = po.amount_tax or 0
        amount_total = po.amount_total or 0

        # Amount in words in Dirhams
        integer_part = int(round(amount_total))
        total_in_words = (
                num2words(integer_part, lang='en').title()
                + " Dirhams Only")


        # === Customer Details for BILL TO ===
        customer = po.partner_id

        customer_name = customer.name or ""
        customer_address = ", ".join(filter(None, [
            customer.street,
            customer.street2,
            customer.city,
            customer.country_id.code if customer.country_id else ""
        ]))
        customer_trn = customer.vat or ""
        customer_phone = customer.phone or ""
        customer_email = customer.email or ""

        # Customer Project Name
        project_name = po.x_studio_customer_project_name if hasattr(po, "x_studio_customer_project_name") else ""

        return {
            "doc_ids": po.ids,
            "doc_model": "purchase.order",
            "docs": po,

            "company": company,

            # PO Info
            "po_number": po_number,
            "po_date": po_date,
            "buyer": buyer,
            "buyer_dept": buyer_dept,
            "buyer_desig": buyer_desig,

            # Vendor Details
            "vendor_name": vendor_name,
            "vendor_address": vendor_address,
            "vendor_trn": vendor_trn,
            "vendor_phone": vendor_phone,
            "vendor_email": vendor_email,

            # Delivery Details
            "place_of_delivery": place_of_delivery,
            "ship_date": ship_date,

            # Lines
            "line_data": line_data,

            # Customer
            "customer_name": customer_name,
            "customer_address": customer_address,
            "customer_trn": customer_trn,
            "customer_phone": customer_phone,
            "customer_email": customer_email,
            "project_name": project_name,

            # Totals dictionary for QWeb
            "totals": {
                "total_excl_vat_sum": amount_untaxed,
                "total_vat_sum": amount_tax,
                "total_incl_vat_sum": amount_total,
                "amount_in_words": total_in_words,
            },
        }
