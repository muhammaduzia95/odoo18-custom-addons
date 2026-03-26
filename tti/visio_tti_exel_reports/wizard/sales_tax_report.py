# tti\visio_tti_exel_reports\wizard\sales_tax_report.py
from odoo import models, fields
import io
import base64
import xlsxwriter


class SalesTaxReportWizard(models.TransientModel):
    _name = 'sales.tax.report.wizard'
    _description = 'Sales Tax Report Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        domain="[('country_id.code', '=', 'PK')]"
    )

    def action_print_pdf_report(self):
        self.ensure_one()
        return self.env.ref('visio_tti_exel_reports.action_report_sales_tax_pdf').report_action(self)

    def action_print_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sales Tax Report')

        # Format header dates
        from_date_str = self.date_from.strftime('%d/%m/%Y') if self.date_from else ''
        to_date_str = self.date_to.strftime('%d/%m/%Y') if self.date_to else ''

        # Formatting
        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        subtitle_format = workbook.add_format({'bold': True, 'font_size': 12})
        header_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', })
        cell_format = workbook.add_format({'border': 1})
        date_format = workbook.add_format({'border': 1, 'num_format': 'd/mmm/yy'})  # For Invoice Date
        amount_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})  # shows 100,000.00

        # Row 1–4 headers
        worksheet.write(0, 0, 'Tti Testing Laboratories', title_format)
        worksheet.write(1, 0, 'Sales Tax Report', subtitle_format)
        worksheet.write(2, 0, 'From')
        worksheet.write(2, 1, from_date_str)
        worksheet.write(3, 0, 'To')
        worksheet.write(3, 1, to_date_str)

        headers = ['Sr #', 'Manufacturer', 'NTN', 'STRN', 'Invoice No.', 'Invoice Date', 'Untaxed Amount', 'Sales Tax',
                   'Total Amount', 'Exchange Rate', 'Currency', 'State', 'Tax Rate']

        # Write headers on row 6 (index 5)
        for col, header in enumerate(headers):
            worksheet.write(5, col, header, header_format)

        # Fetch posted customer invoices in date range
        invoices = self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ])

        row = 6  # Start from row after headers (Excel row 7)
        sr_no = 1

        for inv in invoices:
            partner = inv.partner_id

            worksheet.write(row, 0, sr_no, cell_format)  # Sr #
            worksheet.write(row, 1, partner.name or '', cell_format)  # Manufacturer
            worksheet.write(row, 2, partner.vat or '', cell_format)  # NTN
            worksheet.write(row, 3, partner.strn or '', cell_format)  # STRN
            worksheet.write(row, 4, inv.name or '', cell_format)  # Invoice No.

            if inv.invoice_date:
                worksheet.write_datetime(row, 5, inv.invoice_date, date_format)  # Invoice Date
            else:
                worksheet.write(row, 5, '', cell_format)

            # Default: use invoice values as-is
            untaxed = inv.amount_untaxed
            tax = inv.amount_tax
            total = inv.amount_total

            # Apply conversion if currency ≠ PKR
            if inv.currency_id.name != 'PKR':
                try:
                    to_currency = self.env.ref('base.PKR')
                except ValueError:
                    to_currency = inv.company_id.currency_id  # fallback

                conversion_date = inv.invoice_date or fields.Date.context_today(self)

                # Convert each value separately
                untaxed = inv.currency_id._convert(untaxed, to_currency, inv.company_id, conversion_date)
                tax = inv.currency_id._convert(tax, to_currency, inv.company_id, conversion_date)
                total = inv.currency_id._convert(total, to_currency, inv.company_id, conversion_date)

            # Write converted amounts
            worksheet.write_number(row, 6, round(untaxed, 2), amount_format)  # Untaxed Amount
            worksheet.write_number(row, 7, round(tax, 2), amount_format)  # Sales Tax
            worksheet.write_number(row, 8, round(total, 2), amount_format)  # Total Amount

            # Get exchange rate for non-PKR currencies
            exchange_rate = 1.0
            currency_name = inv.currency_id.name or ''

            if inv.currency_id.name != 'PKR':
                try:
                    to_currency = self.env.ref('base.PKR')
                except ValueError:
                    to_currency = inv.company_id.currency_id  # fallback

                conversion_date = inv.invoice_date or fields.Date.context_today(self)
                exchange_rate = inv.currency_id._convert(
                    1.0, to_currency, inv.company_id, conversion_date
                )

            # Write exchange rate and currency
            worksheet.write(row, 9, round(exchange_rate, 4), cell_format)  # Exchange Rate
            worksheet.write(row, 10, currency_name, cell_format)  # Currency

            # worksheet.write(row, 9, '', cell_format)  # Exchange Rate
            # worksheet.write(row, 10, partner.property_purchase_currency_id.name or '', cell_format)  # Currency
            worksheet.write(row, 11, partner.state_id.name or '', cell_format)  # State
            worksheet.write(row, 12, ', '.join(partner.sales_taxes.mapped('name')) if partner.sales_taxes else '',
                            cell_format)  # Tax Rate

            sr_no += 1
            row += 1

        worksheet.set_column(0, 12, 18)

        workbook.close()
        output.seek(0)
        file_data = output.read()
        filename = 'sales_tax_report.xlsx'

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
