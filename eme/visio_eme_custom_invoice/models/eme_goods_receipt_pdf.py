# D:\Visiomate\Odoo\odoo18\custom_addons\eme\visio_eme_custom_invoice\models\eme_goods_receipt_pdf.py

# -*- coding: utf-8 -*-
from odoo import api, models
from num2words import num2words


class ReportGoodsReceiptPDF(models.AbstractModel):
    _name = "report.visio_eme_custom_invoice.goods_receipt_pdf"
    _description = "EME Goods Receipt Note PDF"

    @api.model
    def _get_report_values(self, docids, data=None):
        # Load purchase order
        picking = self.env['stock.picking'].browse(docids).ensure_one()
        po = picking.purchase_id

        company = picking.company_id
        partner = picking.partner_id

        # --- Basic Header Info ---
        receipt_no = picking.name or ""
        receipt_date = picking.date_done or picking.scheduled_date or False

        # Ship Date from PO field `ship_date`
        ship_date = ""
        if getattr(po, "ship_date", False):
            ship_date = po.ship_date.strftime("%d %b %Y")

        # PO Info
        po_number = po.name
        po_date = po.date_order

        # No source document for GRN from PO
        source_doc = ""

        # --- Partner (Vendor) Info ---
        partner_name = partner.name or ""
        partner_address = ", ".join(filter(None, [
            partner.street,
            partner.street2,
            partner.city,
            partner.country_id.code if partner.country_id else ""
        ]))

        # Prepared By (Buyer)
        salesperson = po.user_id.name or ""
        salesperson_dept = po.user_id.employee_id.department_id.name or ""
        salesperson_desig = po.user_id.employee_id.job_id.name or ""

        # --- GRN Lines from Purchase Order Lines ---
        line_data = []
        counter = 1

        for line in po.order_line:
            vat_percent = sum(line.taxes_id.mapped("amount")) if line.taxes_id else 0.0
            total_excl_vat = line.price_subtotal or 0.0
            vat_amount = total_excl_vat * vat_percent / 100
            total_incl_vat = total_excl_vat + vat_amount

            line_data.append({
                "line_no": counter,
                # what XML expects for "Item code"
                "default_code": line.product_id.default_code or "",
                # description + brand (XML already has brand block)
                "description": line.name or "",
                "brand": getattr(line.product_id.product_tmpl_id, "x_studio_brand", "") or "",
                # UOM + quantities
                "uom": line.product_uom.name or "",
                "qty": line.product_qty or 0.0,
                "received_qty": line.qty_received or 0.0,
                # pricing fields for your existing tbody
                "rate": line.price_unit or 0.0,
                "total_excl_vat": total_excl_vat,
                "vat_percent_display": f"{vat_percent}%" if vat_percent else "-",
                "vat_amount": vat_amount,
                "total_incl_vat": total_incl_vat,
                # still here if you ever need it
                "lot": "",
            })
            counter += 1

        # --- Summary Totals (required by XML even if GRN has no pricing) ---
        totals = {
            "total_qty": sum(l["qty"] for l in line_data),
            "total_received": sum(l["received_qty"] for l in line_data),

            "total_excl_vat_sum": po.amount_untaxed or 0.0,
            "total_vat_sum": po.amount_tax or 0.0,
            "total_incl_vat_sum": po.amount_total or 0.0,
        }

        # Amount in words in Dirhams
        integer_part = int(round(totals["total_incl_vat_sum"] or 0.0))
        total_in_words = (
                num2words(integer_part, lang='en').title()
                + " Dirhams Only"
        )
        totals["amount_in_words"] = total_in_words

        return {
            "doc_ids": picking.ids,
            "doc_model": "stock.picking",
            "docs": picking,
            "company": company,
            "partner": partner,

            # Flag for header switch
            "is_goods_receipt": True,

            # Header Values
            "receipt_no": receipt_no,
            "receipt_date": receipt_date,
            "source_doc": source_doc,
            "po_number": po_number,
            "po_date": po_date,

            # === Prepared By ===
            "salesperson": salesperson,
            "salesperson_dept": salesperson_dept,
            "salesperson_desig": salesperson_desig,

            "partner_name": partner_name,
            "partner_address": partner_address,
            "ship_date": ship_date,

            # Lines & Summary
            "line_data": line_data,
            "totals": totals,
        }
