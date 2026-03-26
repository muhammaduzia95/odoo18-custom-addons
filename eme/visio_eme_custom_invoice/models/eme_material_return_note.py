# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\eme_material_return_note.py

from odoo import models, api
from num2words import num2words


class EMEMaterialReturnNotePDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.material_return_note_pdf'
    _description = 'EME Material Return Note PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(f"[Material Return Note] DocIDs received: {docids}")

        picking = self.env['stock.picking'].browse(docids).ensure_one()
        po = picking.purchase_id

        company = picking.company_id
        partner = picking.partner_id

        # --- Basic Information ---
        company_name = company.name or ""
        buyer = po.user_id.name or ""
        buyer_desig = po.user_id.employee_id.job_id.name or ""
        buyer_dept = po.user_id.employee_id.department_id.name or ""

        mrn_number = picking.name or ""
        mrn_date = picking.date_done or picking.scheduled_date or False

        # --- Vendor / Customer Details ---
        customer_name = partner.name or ""
        customer_address = ", ".join(filter(None, [
            partner.street,
            partner.street2,
            partner.city,
            partner.country_id and partner.country_id.code or ""
        ]))
        customer_trn = partner.vat or ""
        customer_phone = partner.phone or ""
        customer_email = partner.email or ""

        # --- Return Details ---
        place_of_delivery = ""
        ship_date = po.ship_date or ""

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
            "doc_ids": picking.ids,
            "doc_model": "stock.picking",
            "docs": picking,
            "company": company,
            "partner": partner,
            "company_name": company_name,

            # Static Info
            "buyer": buyer,
            "mrn_number": mrn_number,
            "mrn_date": mrn_date,

            # Customer Info
            "customer_name": customer_name,
            "customer_address": customer_address,
            "customer_trn": customer_trn,
            "customer_phone": customer_phone,
            "customer_email": customer_email,

            # Delivery / Return Info
            "place_of_delivery": place_of_delivery,
            "ship_date": ship_date,

            # Lines
            "line_data": line_data,

            "buyer_desig": buyer_desig,
            "buyer_dept": buyer_dept,
        }
