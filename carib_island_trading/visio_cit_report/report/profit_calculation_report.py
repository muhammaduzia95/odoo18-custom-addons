# D:\Visiomate\Odoo\odoo18\custom_addons\carib_island_trading\visio_cit_reports\report\profit_calculation_report.py

# -*- coding: utf-8 -*-
from odoo import models
import io
import base64
import xlsxwriter


class ProfitCalculationReport(models.AbstractModel):
    _name = "profit.calculation.report"
    _description = "Profit Calculation Excel Report"

    def _get_headers(self):
        return [
            "Vendor Cost",
            "Product Sale",
            "Gross Profit",
            "Freight Cost",
            "Freight Charged",
            "Freight Markup",
            "Delivery Cost",
            "Delivery Charged",
            "Delivery Markup",
            "3PL Cost",
            "3PL Charged",
            "3PL Markup",
        ]

    def _build_file(self):
        """Create the XLSX in memory and return raw bytes."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        ws = workbook.add_worksheet("Profit Report")

        header_fmt = workbook.add_format({
            "bold": True,
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        })

        headers = self._get_headers()
        for col, header in enumerate(headers):
            ws.write(0, col, header, header_fmt)

        ws.set_column(0, len(headers) - 1, 18)

        # TODO: add data rows later

        workbook.close()
        output.seek(0)
        return output.read()

    def action_generate_excel(self):
        """Called from server action → returns act_url."""
        file_data = self._build_file()
        filename = "profit_calculation_report.xlsx"

        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(file_data),
            "res_model": "res.users",
            "res_id": self.env.uid,
            "mimetype": (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        })

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }
