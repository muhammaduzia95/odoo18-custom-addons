# \tti\visio_tti_reporting\wizard\daily_summary_wizard.py
from odoo import models, fields
from datetime import date
import io
import base64
import xlsxwriter


class DailySummaryWizard(models.TransientModel):
    _name = 'daily.summary.wizard'
    _description = 'Daily Summary Wizard'

    date_from = fields.Date(string="Date From", required=True, default=lambda self: date.today())
    date_to = fields.Date(string="Date To", required=True, default=lambda self: date.today())

    def action_generate_daily_excel(self):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Daily Summary')

        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'black',
            'border': 1
        })
        data_format = workbook.add_format({'border': 1})
        date_format = workbook.add_format({'border': 1, 'num_format': 'dd/mmm/yy'})  # For Invoice Date

        # Header titles
        headers = [
            'Sr#', 'Month', 'Sale Order Number', 'Manufacturer', 'Buyer',
            'Category', 'Sub Category', 'Tests', 'City', 'City Zone',
            'Salesperson', 'Sale Order Creation date', 'Report Delivery Date', 'Report Status'
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 22)

        # Fetch sale orders (exclude 'cancel')
        sale_orders = self.env['sale.order'].search([
            ('state', 'not in', ['cancel', 'draft', 'sent', 'quotation_done', 'quotation_approved']),
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to)
        ])

        row = 1
        sr = 1
        for so in sale_orders:
            # Dates and formats
            month_str = so.create_date.strftime('%B %Y') if so.create_date else ''
            create_date_str = so.create_date.strftime('%d %B %Y') if so.create_date else ''
            delivery_date_str = so.commitment_date.strftime('%d %B %Y') if so.commitment_date else ''

            # Values
            worksheet.write(row, 0, sr, data_format)  # Sr#
            worksheet.write(row, 1, month_str, data_format)
            worksheet.write(row, 2, so.name or '', data_format)  # Sale Order #
            worksheet.write(row, 3, so.partner_id.name or '', data_format)  # Manufacturer
            worksheet.write(row, 4, so.tti_pi_buyer.name or '', data_format)  # Buyer
            worksheet.write(row, 5, so.tti_si_category.name if so.tti_si_category else '', data_format)  # Category
            worksheet.write(row, 6, so.tti_si_sub_category.name if so.tti_si_sub_category else '',
                            data_format)  # Subcategory

            tests = []
            for line in so.order_line:
                product = line.product_id
                if product.default_code:
                    method = product.tti_test_method
                    if method:
                        tests.append(f"{product.name}")
                    else:
                        tests.append(f"{product.name}")

            tests_str = ', '.join(tests)

            worksheet.write(row, 7, tests_str, data_format)  # Test
            worksheet.write(row, 8, so.partner_id.tti_city_id.name if so.partner_id.tti_city_id else '',
                            data_format)  # City
            worksheet.write(row, 9, so.partner_id.tti_city_zone_id.name if so.partner_id.tti_city_zone_id else '',
                            data_format)  # City Zone
            worksheet.write(row, 10, so.user_id.name or '', data_format)  # Salesperson
            # worksheet.write(row, 11, create_date_str, data_format)  # SO Creation Date
            # worksheet.write(row, 12, delivery_date_str, data_format)  # Delivery Date

            if so.create_date:
                worksheet.write_datetime(row, 11, so.create_date, date_format)
            else:
                worksheet.write(row, 11, '', data_format)

            if so.commitment_date:
                worksheet.write_datetime(row, 12, so.commitment_date, date_format)
            else:
                worksheet.write(row, 12, '', data_format)

            worksheet.write(row, 13, so.state or '', data_format)  # Status

            row += 1
            sr += 1

        workbook.close()
        output.seek(0)

        report_data = base64.b64encode(output.read())
        attachment = self.env['ir.attachment'].create({
            'name': 'Daily Summary Report.xlsx',
            'type': 'binary',
            'datas': report_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
