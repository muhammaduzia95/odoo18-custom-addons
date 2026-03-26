# \tti\visio_tti_reporting\wizard\daily_ledger_wizard.py
from odoo import models, fields
import io
import base64
import xlsxwriter
from datetime import date, timedelta


class DailyLedgerWizard(models.TransientModel):
    _name = 'daily.ledger.wizard'
    _description = 'Daily Ledger Wizard'

    date_from = fields.Date(string="Date From", required=True, default=lambda self: date.today())
    date_to = fields.Date(string="Date To", required=True, default=lambda self: date.today())
    customer = fields.Many2one('res.partner', string="Customer",
                               domain="[('employee', '=' , False), ('customer_rank','>',0)]")

    def action_generate_ledger_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Daily Ledger')

        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'black',
            'border': 1
        })

        headers = ['Sr#', 'Date', 'Sale Order Number', 'Invoice#', 'Manufacturer', 'Buyer', 'Agent', 'Gross Amount',
                   'Extra Charges', 'Discount', 'Sub Total', 'Sales Tax', 'Net Amount', ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        # Data Format
        data_format = workbook.add_format({'border': 1})
        amount_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        date_format = workbook.add_format({'border': 1, 'num_format': 'dd/mmm/yy'})  # For Invoice Date

        # Fetch sale orders
        domain = [
            ('state', 'in', ['sale', 'done']),  # only Sales Orders (confirmed/locked)
            ('date_order', '>=', self.date_from),
            ('date_order', '<', self.date_to + timedelta(days=1)),
            ('company_id', '=', self.env.company.id),
        ]

        if self.customer:
            domain.append(('partner_id', '=', self.customer.id))

        sale_orders = self.env['sale.order'].sudo().search(domain, order='date_order,id')

        row = 1
        sr = 1
        pkr_currency = self.env.ref('base.PKR')

        for so in sale_orders:
            def to_pkr(amount):
                return amount if so.currency_id == pkr_currency else so.currency_id._convert(
                    amount, pkr_currency, so.company_id, so.date_order)

            invoices = so.order_line.mapped('invoice_lines.move_id').filtered(
                lambda inv: inv.move_type == 'out_invoice' and inv.state != 'cancel'
            )
            if not invoices:
                invoices = [None]

            for inv in invoices:
                date_str = (inv.create_date if inv else so.create_date).strftime('%d %B %Y') if (
                        inv or so.create_date) else ''

                state_code = so.partner_id.state_id.code if so.partner_id.state_id else ''
                invoice_name = inv.name if inv else f"{(state_code[:1].upper() if state_code else '0')}-000000-000000"

                manufacturer = inv.partner_id.name if inv else so.partner_id.name
                buyer = so.tti_pi_buyer.name if so.tti_pi_buyer else ''
                agent = so.tti_pi_agent_id.name if so.tti_pi_agent_id else ''

                gross_amount = sum(
                    to_pkr(l.product_uom_qty * l.price_unit)
                    for l in so.order_line
                    if l.product_id and l.product_id.default_code
                )

                manual_discount = sum(
                    to_pkr(l.price_unit * l.product_uom_qty * (l.discount / 100))
                    for l in so.order_line if l.discount
                )
                global_discount = sum(
                    to_pkr(abs(l.price_subtotal))
                    for l in so.order_line
                    if
                    l.product_id.product_tmpl_id and l.product_id.product_tmpl_id.name.lower() == 'discount' and l.price_unit < 0
                )
                total_discount = manual_discount + global_discount

                worksheet.write(row, 0, sr, data_format)
                # worksheet.write(row, 1, date_str, date_format)

                if inv and inv.create_date:
                    worksheet.write_datetime(row, 1, inv.create_date, date_format)
                else:
                    worksheet.write_datetime(row, 1, so.create_date, date_format)

                worksheet.write(row, 2, so.name or '', data_format)
                worksheet.write(row, 3, invoice_name, data_format)
                worksheet.write(row, 4, manufacturer or '', data_format)
                worksheet.write(row, 5, buyer, data_format)
                worksheet.write(row, 6, agent, data_format)
                worksheet.write_number(row, 7, gross_amount, amount_format)
                worksheet.write_number(row, 8, to_pkr(so.tti_total_charges or 0.0), amount_format)
                worksheet.write_number(row, 9, total_discount, amount_format)
                worksheet.write_number(row, 10, to_pkr(so.amount_untaxed), amount_format)
                worksheet.write_number(row, 11, to_pkr(so.amount_tax), amount_format)
                worksheet.write_number(row, 12, to_pkr(so.amount_total), amount_format)

                row += 1
                sr += 1

        print(f"✅ Ledger Report Generated. Rows written: {sr - 1}")
        workbook.close()
        output.seek(0)

        report_data = base64.b64encode(output.read())
        attachment = self.env['ir.attachment'].create({
            'name': 'Daily Ledger Report.xlsx',
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
