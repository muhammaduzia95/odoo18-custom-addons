from odoo import models, api
from num2words import num2words


class EMEProformaServicePDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.material_issue_note_pdf'
    _description = 'EME Material Issue Note PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(f"DocIDs received: {docids}")

        po = self.env['purchase.order'].browse(docids).ensure_one()

        company = po.company_id
        partner = po.partner_id

        # --- Fetch key data ---
        company_name = company.name or ""
        buyer = po.user_id.name or ""
        buyer_desig = po.user_id.employee_id.job_id.name or ""
        buyer_dept = po.user_id.employee_id.department_id.name or ""
        in_number = po.name or ""
        in_date = po.date_order or ""

        # Ship Date from PO field: ship_date
        ship_date = ""
        if getattr(po, "ship_date", False):
            ship_date = po.ship_date.strftime("%d %b %Y")

        # --- Bill To (Customer) Details ---
        customer_name = partner.name or ""
        customer_address = ", ".join(filter(None, [
            partner.street,
            partner.street2,
            partner.city,
            partner.country_id and partner.country_id.code or ""
        ]))
        project_name = ""
        customer_trn = partner.vat or ""
        customer_phone = partner.phone or ""
        customer_email = partner.email or ""

        # --- Ship To Details ---
        place_of_delivery = ""

        # --- Line Items ---
        line_data = []

        for index, line in enumerate(po.order_line, start=1):
            line_data.append({
                "line_no": index,
                "default_code": line.product_id.default_code or "-",
                "description": line.name or "",
                "brand": getattr(line.product_id.product_tmpl_id, "x_studio_brand", "") or "",
                "uom": line.product_uom.name or "",
                "qty": line.product_qty or 0.0,
            })

        return {
            "doc_ids": po.ids,
            "doc_model": "purchase.order",
            "docs": po,
            "company": company,
            "partner": partner,
            "company_name": company_name,

            # Static Info
            "buyer": buyer,
            "in_number": in_number,
            "in_date": in_date,

            # Bill To
            "customer_name": customer_name,
            "customer_address": customer_address,
            "project_name": project_name,
            "customer_trn": customer_trn,
            "customer_phone": customer_phone,
            "customer_email": customer_email,

            # Ship To
            "place_of_delivery": place_of_delivery,
            "ship_date": ship_date,

            # Invoice Lines
            'line_data': line_data,

            "buyer_desig": buyer_desig,
            "buyer_dept": buyer_dept,
        }
