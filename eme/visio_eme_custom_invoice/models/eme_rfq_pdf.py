# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\eme_rfq_pdf.py
from odoo import models, api
from num2words import num2words


class EMERFQPDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.rfq_pdf'
    _description = 'EME Request for Quotation PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(f"[RFQ PDF] DocIDs received: {docids}")

        rfq = self.env['purchase.order'].browse(docids).ensure_one()

        company = rfq.company_id
        vendor = rfq.partner_id

        # --- Basic Information ---
        company_name = company.name or ""
        buyer = rfq.user_id.name or ""
        buyer_desig = rfq.user_id.employee_id.job_id.name or ""
        buyer_dept = rfq.user_id.employee_id.department_id.name or ""

        rfq_number = rfq.name or ""
        rfq_date = rfq.date_order or ""

        # --- Vendor Details ---
        vendor_name = vendor.name or ""
        vendor_address = ", ".join(filter(None, [
            vendor.street,
            vendor.street2,
            vendor.city,
            vendor.country_id and vendor.country_id.code or ""
        ]))
        vendor_trn = vendor.vat or ""
        vendor_phone = vendor.phone or ""
        vendor_email = vendor.email or ""

        # --- Delivery Info ---
        place_of_delivery = ""
        ship_date = ""

        # --- Line Items ---
        line_data = []

        for index, line in enumerate(rfq.order_line, start=1):
            line_data.append({
                "line_no": index,
                "default_code": line.product_id.default_code or "-",
                "description": line.name or "",
                "brand": getattr(line.product_id.product_tmpl_id, "x_studio_brand", "") or "",
                "uom": line.product_uom.name or "",
                "qty": line.product_qty or 0.0,
            })

        return {
            "doc_ids": rfq.ids,
            "doc_model": "purchase.order",
            "docs": rfq,
            "company": company,
            "vendor": vendor,
            "company_name": company_name,

            # Static Info
            "buyer": buyer,
            "rfq_number": rfq_number,
            "rfq_date": rfq_date,

            # Vendor Details
            "vendor_name": vendor_name,
            "vendor_address": vendor_address,
            "vendor_trn": vendor_trn,
            "vendor_phone": vendor_phone,
            "vendor_email": vendor_email,

            # Delivery Details
            "place_of_delivery": place_of_delivery,
            "ship_date": ship_date,

            # RFQ Lines
            "line_data": line_data,

            "buyer_desig": buyer_desig,
            "buyer_dept": buyer_dept,
        }
