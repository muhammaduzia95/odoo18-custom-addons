from odoo import models, api
from num2words import num2words


class EMEProformaServicePDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.delivery_note_pdf'
    _description = 'EME Tax Credit Note PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("\n==================== GENERATING EME Delivery Note ====================")
        print(f"DocIDs received: {docids}")

        picking = self.env['stock.picking'].browse(docids).ensure_one()
        print("Picking found", picking)

        so = picking.sale_id  # related sale order (may be False if not from SO)

        company = picking.company_id
        partner = picking.partner_id

        # --- Fetch key data ---
        company_name = company.name or ""
        salesperson = so.user_id.name or ""
        salesperson_desig = so.user_id.employee_id.job_id.name or ""
        salesperson_dept = so.user_id.employee_id.department_id.name or ""
        po_number = so.customer_po_no or "" if so else ""

        po_date = ""
        if so and so.customer_po_date:
            po_date = so.customer_po_date.strftime("%d %b %Y")

        ship_date = ""
        if so and so.ship_date:
            ship_date = so.ship_date.strftime("%d %b %Y")

        dn_date = picking.date_done or picking.scheduled_date or False
        quote_no = so.name or "" if so else ""
        delivery_note_no = picking.name or ""

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

        # --- Line Items ---
        line_data = []

        for index, line in enumerate(so.order_line, start=1):
            line_data.append({
                "line_no": index,
                "default_code": line.product_id.default_code or "-",
                "description": line.name or "",
                "brand": getattr(line.product_template_id, "x_studio_brand", "") or "",
                "uom": line.product_uom.name or "",
                "qty": line.product_uom_qty or 0.0,

            })

        return {
            "doc_ids": picking.ids,
            "doc_model": "stock.picking",
            "docs": picking,
            "company": company,
            "partner": partner,
            "company_name": company_name,

            # Static Info
            "salesperson": salesperson,
            "po_number": po_number,
            "po_date": po_date,
            "dn_date": dn_date,
            "quote_no": quote_no,
            "delivery_note_no": delivery_note_no,

            # Bill To
            "customer_name": customer_name,
            "customer_address": customer_address,
            "project_name": project_name,
            "customer_trn": customer_trn,
            "customer_phone": customer_phone,
            "customer_email": customer_email,

            # Ship To
            "ship_date": ship_date,

            # Invoice Lines
            'line_data': line_data,

            "salesperson_dept": salesperson_dept,
            "salesperson_desig": salesperson_desig,

        }
