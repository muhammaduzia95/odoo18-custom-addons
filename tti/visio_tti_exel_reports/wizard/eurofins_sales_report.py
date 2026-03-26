from odoo import models, fields
from datetime import datetime
import base64
import io
import xlsxwriter


class EurofinsSalesReportWizard(models.TransientModel):
    _name = 'eurofins.sales.report.wizard'
    _description = 'Eurofins Sales Report'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)

    def action_download_excel(self):
        # Prepare Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Report')

        # Define bold header format with border
        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',  # Horizontal center
            'valign': 'vcenter'  # Vertical center
        })

        headers = [
            'Order Date', 'Reference No', 'Invoice Date', 'Sales Tax Invoice #', 'Buyer Name',
            'Customer Name', 'Category', 'City', 'City Zone', 'Amount Rs.', 'Sales Tax'
        ]
        for col, header in enumerate(headers):
            # worksheet.write(0, col, header)
            worksheet.write(5, col, header, header_format)  # Zia

        # Fetch invoices
        invoices = self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('sale_order_ids', '!=', False),
        ])

        # Format dates nicely
        from_date_str = self.date_from.strftime('%d %b, %Y') if self.date_from else ''
        to_date_str = self.date_to.strftime('%d %b, %Y') if self.date_to else ''

        # Formats
        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        subtitle_format = workbook.add_format({'bold': True, 'font_size': 12})
        total_format = workbook.add_format({
            'bottom': 1,
            'bold': True,
            'num_format': '#,##0.00'
        })

        # Row 1 & 2
        worksheet.write(0, 0, 'Textile Testing International', title_format)
        worksheet.write(1, 0, 'Sales Report - Eurofins/MTS', subtitle_format)

        # Row 3 & 4
        worksheet.write(2, 0, 'Period from:')
        worksheet.write(2, 1, from_date_str)
        worksheet.write(3, 0, 'Period to:')
        worksheet.write(3, 1, to_date_str)

        # Define border format for data rows
        cell_format = workbook.add_format({'border': 1})
        date_format = workbook.add_format({'num_format': 'd/mmm/yy', 'border': 1})  # This gives: 3/Apr/25
        amount_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})  # shows 100,000.00

        # row = 1  # Start from second row
        row = 6  # Start from second row # Zia
        for invoice in invoices:
            for so in invoice.sale_order_ids:
                if so.tti_si_select_partner != 'mts':
                    continue

                # Fetch buyer, partner, category, city/zone
                partner = so.partner_id
                buyer_name = so.tti_pi_buyer.name if so.tti_pi_buyer else ''
                category = so.tti_si_category.name or ''
                city = partner.tti_city_id.name if partner.tti_city_id else ''
                city_zone = partner.tti_city_zone_id.name if partner.tti_city_zone_id else ''

                # Get untaxed amount from invoice, converted to PKR if needed
                amount = (so.amount_untaxed or 0.0) - (so.tti_total_charges or 0.0)
                if (so.currency_id and so.currency_id.name != 'PKR'):
                    date = so.date_order or fields.Date.context_today(self)
                    rate = so.currency_id._convert(
                        1.0, self.env.ref('base.PKR'), so.company_id, date
                    )
                    amount *= rate

                # Get tax name from any SO line
                tax_name = ''
                if so.order_line:
                    taxes = so.order_line[0].tax_id
                    tax_name = taxes[0].name if taxes else ''

                # Write row
                # worksheet.write(row, 0, so.date_order.strftime('%Y-%m-%d') if so.date_order else '', cell_format)
                if so.date_order:
                    worksheet.write_datetime(row, 0, so.date_order, date_format)
                else:
                    worksheet.write(row, 0, '', cell_format)

                worksheet.write(row, 1, so.name or '', cell_format)

                # Invoice Date
                if invoice.invoice_date:
                    worksheet.write_datetime(row, 2, datetime.combine(invoice.invoice_date, datetime.min.time()),
                                             date_format)
                else:
                    worksheet.write(row, 2, '', cell_format)

                worksheet.write(row, 3, invoice.name or '', cell_format)
                worksheet.write(row, 4, buyer_name, cell_format)
                worksheet.write(row, 5, partner.name or '', cell_format)
                worksheet.write(row, 6, category, cell_format)
                worksheet.write(row, 7, city, cell_format)
                worksheet.write(row, 8, city_zone, cell_format)
                worksheet.write(row, 9, round(amount, 2), amount_format)
                worksheet.write(row, 10, tax_name, cell_format)
                row += 1

        # Total row -------
        amount_col_letter = 'J'
        start_row = 7
        end_row = row

        _logger = __import__('logging').getLogger(__name__)
        _logger.info("Generating total for column %s from row %s to row %s", amount_col_letter, start_row, end_row)

        # Recalculate total amount: (SO untaxed − total charges), converted to PKR if needed
        total_amount = 0.0
        for invoice in invoices:
            for so in invoice.sale_order_ids:
                if so.tti_si_select_partner != 'mts':
                    continue

                amount = (so.amount_untaxed or 0.0) - (so.tti_total_charges or 0.0)

                # Use SO currency for conversion if available; else fall back to invoice currency
                src_currency = so.currency_id or invoice.currency_id
                if src_currency and src_currency.name != 'PKR':
                    date = so.date_order or fields.Date.context_today(self)
                    try:
                        rate = src_currency._convert(1.0, self.env.ref('base.PKR'), so.company_id or invoice.company_id,
                                                     date)
                        amount *= rate
                    except Exception:
                        pass

                total_amount += amount

        _logger.info("Final total amount calculated: %s", total_amount)

        # Write hardcoded total instead of formula
        worksheet.write(row, 9, round(total_amount, 2), total_format)

        workbook.close()
        output.seek(0)

        # Create attachment and trigger download
        file_data = output.read()
        filename = 'eurofins_sales_report.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
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
