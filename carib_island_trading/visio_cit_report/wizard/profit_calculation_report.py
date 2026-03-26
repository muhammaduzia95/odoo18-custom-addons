# D:\Visiomate\Odoo\odoo18\custom_addons\carib_island_trading\visio_cit_report\wizard\profit_calculation_report.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api
import io
import base64
import xlsxwriter


class ProfitReportWizard(models.TransientModel):
    _name = "profit.report.wizard"
    _description = "Profit Calculation Wizard"

    sales_rep_id = fields.Many2one(
        'res.users',
        string="Sales Rep Name",
        related='sale_order_id.user_id',
        store=True,
        help="Sales representative (same as Sale Order user_id).",
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        domain="[('state', 'in', ['sale', 'done'])]",
        help="Select only confirmed or completed Sale Orders.",
    )

    commission_amount = fields.Float(
        string="Commission Amount ($)",
        help="Commission amount in USD (or company currency).",
    )

    def action_generate_excel(self):
        """Generate Excel report with vertical headers and formulas (starting at B2)."""
        self.ensure_one()

        def _to_float(value):
            try:
                return float(value or 0.0)
            except (TypeError, ValueError):
                return 0.0

        so = self.sale_order_id
        po = self.env["purchase.order"].search([("origin", "=", so.name)], limit=1) if so else False

        # ---------- PRODUCT SALE & FREIGHT CHARGED FROM SO LINES ----------
        # Product Sale = all lines EXCEPT "Logistics Services"
        # Freight Charged = ONLY "Logistics Services"
        product_lines = self.env["sale.order.line"]
        logistics_lines = self.env["sale.order.line"]

        if so:
            product_lines = so.order_line.filtered(
                lambda l: not l.categ_id or l.categ_id.name != "Logistics Services"
            )
            logistics_lines = so.order_line.filtered(
                lambda l: l.categ_id and l.categ_id.name == "Logistics Services"
            )

        product_sale = sum(product_lines.mapped("price_subtotal"))
        freight_charged_val = sum(logistics_lines.mapped("price_subtotal"))

        # ---------- RAW NUMBERS FROM PO + WIZARD ----------
        vendor_cost = _to_float(po.amount_total if po else 0.0)  # Vendor Cost = PO Total
        freight_cost = _to_float(getattr(po, "freight_cost", 0.0) if po else 0.0)
        delivery_cost = _to_float(getattr(po, "delivery_cost", 0.0) if po else 0.0)
        delivery_charged = _to_float(getattr(po, "delivery_charged", 0.0) if po else 0.0)
        tpl_cost = _to_float(getattr(po, "tpl_cost", 0.0) if po else 0.0)
        tpl_charged = _to_float(getattr(po, "third_party_logistics_col", 0.0) if po else 0.0)
        commission = _to_float(self.commission_amount)

        # ------------------------------------------------------------------
        # Create workbook in memory
        # ------------------------------------------------------------------
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('Profit Report')

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter'
        })

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        })
        value_format = workbook.add_format({'border': 1, 'align': 'center',})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'align': 'center'})

        col_h = 1  # Column B
        col_v = 2  # Column C

        def cell_c(row_index):
            return f'C{row_index + 1}'  # convert 0-based row to Excel cell (column C)


        # --------------------------------------------------------------
        # SECTION 1 — TOP FIELDS (B2 downwards)
        # --------------------------------------------------------------
        # Row 2 = merged title B2:C2
        ws.merge_range(1, 1, 1, 2, "Profit Margin Report", title_format)

        # Start actual report from Row 4
        row = 3
        ws.write(row, col_h, "Sale Order #", header_format)
        ws.write(row, col_v, so.name if so else "", value_format)
        row += 1

        ws.write(row, col_h, "Sales Rep", header_format)
        ws.write(row, col_v, self.sales_rep_id.name or "", value_format)
        row += 1

        commission_row = row
        ws.write(row, col_h, "Commission Amount", header_format)
        ws.write_number(row, col_v, commission, number_format)
        row += 1

        row += 1  # blank row

        # --------------------------------------------------------------
        # SECTION 2 — PROFIT DETAILS
        # --------------------------------------------------------------
        vendor_row = row
        ws.write(row, col_h, "Vendor Cost", header_format)
        ws.write_number(row, col_v, vendor_cost, number_format)
        row += 1

        product_row = row
        ws.write(row, col_h, "Product Sale", header_format)
        ws.write_number(row, col_v, product_sale, number_format)
        row += 1

        gross_row = row
        ws.write(row, col_h, "Gross Profit", header_format)
        ws.write_formula(row, col_v,
                         f'={cell_c(product_row)}-{cell_c(vendor_row)}',
                         number_format)
        row += 1

        freight_cost_row = row
        ws.write(row, col_h, "Freight Cost", header_format)
        ws.write_number(row, col_v, freight_cost, number_format)
        row += 1

        freight_charged_row = row
        ws.write(row, col_h, "Freight Charged", header_format)
        ws.write_number(row, col_v, freight_charged_val, number_format)
        row += 1

        freight_markup_row = row
        ws.write(row, col_h, "Freight Markup", header_format)
        ws.write_formula(row, col_v,
                         f'={cell_c(freight_charged_row)}-{cell_c(freight_cost_row)}',
                         number_format)
        row += 1

        delivery_cost_row = row
        ws.write(row, col_h, "Delivery Cost", header_format)
        ws.write_number(row, col_v, delivery_cost, number_format)
        row += 1

        delivery_charged_row = row
        ws.write(row, col_h, "Delivery Charged", header_format)
        ws.write_number(row, col_v, delivery_charged, number_format)
        row += 1

        delivery_markup_row = row
        ws.write(row, col_h, "Delivery Markup", header_format)
        ws.write_formula(row, col_v,
                         f'={cell_c(delivery_charged_row)}-{cell_c(delivery_cost_row)}',
                         number_format)
        row += 1

        tpl_cost_row = row
        ws.write(row, col_h, "3PL Cost", header_format)
        ws.write_number(row, col_v, tpl_cost, number_format)
        row += 1

        tpl_charged_row = row
        ws.write(row, col_h, "3PL Charged", header_format)
        ws.write_number(row, col_v, tpl_charged, number_format)
        row += 1

        tpl_markup_row = row
        ws.write(row, col_h, "3PL Markup", header_format)
        # as per your formula: (3PL Cost - 3PL Charged)
        ws.write_formula(row, col_v,
                         f'={cell_c(tpl_cost_row)}-{cell_c(tpl_charged_row)}',
                         number_format)
        row += 1

        row += 1  # blank row

        # --------------------------------------------------------------
        # SECTION 3 — FINAL CALCULATIONS
        # --------------------------------------------------------------
        final_profit_row = row
        ws.write(row, col_h, "Final Profit", header_format)
        ws.write_formula(
            row, col_v,
            f'=({cell_c(gross_row)}+{cell_c(freight_markup_row)})'
            f'-({cell_c(delivery_markup_row)}+{cell_c(tpl_markup_row)})',
            number_format,
        )
        row += 1

        final_margin_row = row
        ws.write(row, col_h, "Final Margin %", header_format)
        ws.write_formula(
            row, col_v,
            f'={cell_c(final_profit_row)}/({cell_c(product_row)}+{cell_c(freight_charged_row)})',
            number_format,
        )
        row += 1

        row += 1  # blank row

        # --------------------------------------------------------------
        # SECTION 4 — AFTER COMMISSION
        # --------------------------------------------------------------
        final_profit_comm_row = row
        ws.write(row, col_h, "Final Profit After Commission", header_format)
        ws.write_formula(
            row, col_v,
            f'={cell_c(final_profit_row)}-{cell_c(commission_row)}',
            number_format,
        )
        row += 1

        ws.write(row, col_h, "Final Margin After Commission", header_format)
        ws.write_formula(
            row, col_v,
            f'={cell_c(final_profit_comm_row)}/({cell_c(product_row)}+{cell_c(freight_charged_row)})',
            number_format,
        )
        row += 1

        ws.set_column(1, 2, 35)

        workbook.close()
        output.seek(0)
        file_data = output.read()

        attachment = self.env['ir.attachment'].create({
            'name': 'profit_calculation_report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
