# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\eme_material_request_pdf.py

from odoo import models, api
from num2words import num2words


class EMEMaterialRequestPDF(models.AbstractModel):
    _name = 'report.visio_eme_custom_invoice.material_request_pdf'
    _description = 'EME Material Request PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(f"[MATERIAL REQUEST PDF] DocIDs received: {docids}")

        mr = self.env['purchase.order'].browse(docids).ensure_one()

        company = mr.company_id
        requester = mr.user_id
        partner = mr.partner_id  # optional (if needed)

        # --- Basic Info ---
        company_name = company.name or ""
        requester_name = requester.name or ""
        requester_desig = requester.employee_id.job_id.name or ""
        requester_dept = requester.employee_id.department_id.name or ""

        mr_number = mr.name or ""
        mr_date = mr.date_order or ""
        project_name = mr.project_id.name or ""

        # --- Requester/Department Details ---
        dept_name = requester.employee_id.department_id.name or ""

        # --- Delivery / Project Info ---
        place_of_delivery = ""
        needed_date = ""

        # --- Line Items ---
        line_data = []

        for index, line in enumerate(mr.order_line, start=1):
            line_data.append({
                "line_no": index,
                "default_code": line.product_id.default_code or "-",
                "description": line.name or "",
                "brand": getattr(line.product_id.product_tmpl_id, "x_studio_brand", "") or "",
                "uom": line.product_uom.name or "",
                "qty": line.product_qty or 0.0,
            })

        return {
            "doc_ids": mr.ids,
            "doc_model": "purchase.order",
            "docs": mr,
            "company": company,
            "company_name": company_name,

            # Static Info
            "requester_name": requester_name,
            "requester_desig": requester_desig,
            "requester_dept": requester_dept,

            "mr_number": mr_number,
            "mr_date": mr_date,
            "project_name": project_name,

            # === Prepared By (Buyer) ===
            "buyer": requester_name,
            "buyer_dept": requester_dept,
            "buyer_desig": requester_desig,

            # Delivery Info
            "place_of_delivery": place_of_delivery,
            "needed_date": needed_date,

            # Lines
            "line_data": line_data,
        }
