import io
import base64
import xlsxwriter
from odoo import models, fields
from datetime import date


class InvoiceDailySummaryWizard(models.TransientModel):
    _name = 'invoice.daily.summary.wizard'
    _description = 'Invoice Daily Summary Wizard'

    date_from = fields.Date(string="Date From", required=True, default=lambda self: date.today())
    date_to = fields.Date(string="Date To", required=True, default=lambda self: date.today())

    def action_generate_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Report')

        # Styles
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        header_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_color': 'white', 'bg_color': '#548235',
             'border': 1})
        data_format = workbook.add_format({'border': 1})
        amount_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})  # shows 100,000.00
        date_format = workbook.add_format({'border': 1, 'num_format': 'dd/mmm/yy'})

        # Title
        worksheet.merge_range('A1:L1', 'Invoice Daily Summary Report', title_format)

        # Headers
        headers = [
            'Sr#', 'Category', 'Sale order#', 'Invoice#', 'Total Amount',
            'Company Name', 'Buyer Name', 'City', 'Zone', 'Reg. By',
            'Order Creation date', 'Delivery Date',
        ]
        for col, header in enumerate(headers):
            worksheet.write(1, col, header, header_format)
            worksheet.set_column(col, col, 20)

        # Fetch posted invoices for selected date
        invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>', self.date_from),
            ('invoice_date', '<', self.date_to)
        ])

        row = 2
        count = 1
        for inv in invoices:
            sale_orders = inv.invoice_line_ids.mapped('sale_line_ids.order_id')
            if not sale_orders:
                continue  # Safety check

            # Aggregate values from sale orders
            sale_order_names = ', '.join(sorted(set(s.name for s in sale_orders if s.name)))
            # order_dates = ', '.join(sorted(set(s.date_order.strftime('%Y-%m-%d') for s in sale_orders if s.date_order)))
            # delivery_dates = ', '.join(
            #     sorted(set(s.commitment_date.strftime('%Y-%m-%d') for s in sale_orders if s.commitment_date)))

            order_date_vals = sorted(set(s.date_order for s in sale_orders if s.date_order))
            delivery_date_vals = sorted(set(s.commitment_date for s in sale_orders if s.commitment_date))

            # cities = ', '.join(sorted(set(s.partner_id.tti_city_id or '' for s in sale_orders)))
            city_names = sorted({s.partner_id.tti_city_id.name for s in sale_orders if s.partner_id.tti_city_id})
            cities = ', '.join(city_names)

            salespersons = ', '.join(sorted(set(s.user_id.name or '' for s in sale_orders)))
            categories = ', '.join(sorted(set(s.tti_si_category.name for s in sale_orders if s.tti_si_category)))
            companies = ', '.join(sorted(set(s.partner_id.name or '' for s in sale_orders)))
            buyer_refs = ', '.join(sorted(set(s.tti_pi_buyer.name or '' for s in sale_orders)))
            zones = ', '.join(sorted(
                set(s.partner_id.tti_city_zone_id.name or '' for s in sale_orders if s.partner_id.tti_city_zone_id)))

            # Write row
            worksheet.write(row, 0, count, data_format)  # Sr#
            worksheet.write(row, 1, categories, data_format)  # Category
            worksheet.write(row, 2, sale_order_names, data_format)
            worksheet.write(row, 3, inv.name, data_format)  # Invoice#
            worksheet.write(row, 4, inv.amount_total, amount_format)  # Total
            worksheet.write(row, 5, companies, data_format)  # Company Name
            worksheet.write(row, 6, buyer_refs, data_format)  # Buyer Name
            worksheet.write(row, 7, cities, data_format)
            worksheet.write(row, 8, zones, data_format)  # Zone
            worksheet.write(row, 9, salespersons, data_format)
            # worksheet.write(row, 10, order_dates, data_format)
            # worksheet.write(row, 11, delivery_dates, data_format)

            # For Order Creation Date
            if order_date_vals:
                worksheet.write_datetime(row, 10, order_date_vals[0], date_format)  # earliest date
            else:
                worksheet.write(row, 10, '', data_format)

            # For Delivery Date
            if delivery_date_vals:
                worksheet.write_datetime(row, 11, delivery_date_vals[0], date_format)
            else:
                worksheet.write(row, 11, '', data_format)

            count += 1
            row += 1

        workbook.close()
        output.seek(0)

        report_data = base64.b64encode(output.read())
        attachment = self.env['ir.attachment'].create({
            'name': 'Invoice Daily Summary.xlsx',
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
