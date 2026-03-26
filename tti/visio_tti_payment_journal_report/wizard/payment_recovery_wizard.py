# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_payment_journal_report\wizard\payment_recovery_wizard.py
import base64
import io
import xlsxwriter
from odoo import models, fields


class PaymentRecoveryWizard(models.TransientModel):
    _name = 'payment.recovery.wizard'
    _description = 'Payment Recovery Report Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)

    def action_print_excel(self):
        import base64
        import io
        import xlsxwriter

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Recovery Report")

        # ===== FORMATS =====
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        subtitle_format = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'})
        date_label_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        date_value_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#C0C0C0'})
        section_title_format = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'left'})
        cell_format = workbook.add_format({'border': 1})
        date_cell_format = workbook.add_format({'border': 1, 'num_format': 'dd-mmm-yyyy'})
        subtotal_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'right'})

        # ===== MERGED TITLES =====
        sheet.merge_range("A1:J1", "TTI Testing Laboratories", title_format)
        sheet.merge_range("A2:J2", "Recovery Detail", subtitle_format)

        # ===== DATE ROW =====
        date_from_str = self.date_from.strftime('%d %b, %Y')
        date_to_str = self.date_to.strftime('%d %b, %Y')

        sheet.write("D4", "Date From:", date_label_format)
        sheet.write("E4", date_from_str, date_value_format)

        sheet.write("F4", "Date To:", date_label_format)
        sheet.write("G4", date_to_str, date_value_format)

        # ===== UNIFORM WIDTH (10 cols) =====
        for col in range(10):
            sheet.set_column(col, col, 18)

        # ===== HEADERS =====
        headers = [
            "ID", "Date", "Customer Name", "Instrument #", "Bill No",
            "Amount", "Sale Tax.", "Invoice Tax", "Total Amount", "Comments"
        ]

        def write_headers(row):
            for col, h in enumerate(headers):
                sheet.write(row, col, h, header_format)

        # Start writing below row 6
        current_row = 6

        # Section mappings
        sections = [
            ("Cash", "cash"),
            ("Cheque", "cheque"),
            ("Online Transfer", "online")
        ]

        # Fetch payments once
        payments = self.env['account.payment'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ], order="date asc")

        subtotal_rows = []

        # ===== PROCESS EACH PAYMENT CATEGORY =====
        for title, category in sections:

            # Filter section payments
            section_payments = payments.filtered(lambda p: p.payment_category == category)

            if not section_payments:
                continue

            # Section title
            sheet.write(current_row, 0, title, section_title_format)
            current_row += 1

            # Headers row
            write_headers(current_row)
            current_row += 1

            # Mark starting row of data
            start_row_fixed = current_row + 1  # +1 because Excel formulas start counting from 1

            # Write section rows
            excel_start_row = current_row + 1  # Excel is 1-indexed

            for pay in section_payments:

                # ===== COL 1 — ID =====
                sheet.write(current_row, 0, pay.move_id.name or "", cell_format)

                # ===== COL 2 — Date =====
                if pay.date:
                    sheet.write_datetime(current_row, 1, pay.date, date_cell_format)
                else:
                    sheet.write(current_row, 1, "", cell_format)

                # ===== COL 3 — Customer Name =====
                sheet.write(current_row, 2, pay.partner_id.name or "", cell_format)

                # ===== COL 4 — Instrument # =====
                sheet.write(current_row, 3, pay.move_id.instr_no or "", cell_format)

                # ===== COL 5 — Bill No =====
                sheet.write(current_row, 4, pay.move_id.bill_no or "", cell_format)

                # ===== COL 6 — Amount =====
                sheet.write_number(current_row, 5, pay.amount, cell_format)

                # ===== COL 7 — Sale Tax =====
                sale_tax = pay.sal_tax_wh or 0.0
                sale_acc = pay.sale_wh_tax_account

                # if tti_report_type is "default" or blank -> show 0
                if not sale_acc or sale_acc.tti_report_type in ('default', False, ''):
                    sale_tax = 0.0

                sheet.write_number(current_row, 6, sale_tax, cell_format)

                # ===== COL 8 — Income Tax =====
                income_tax = pay.income_tax_wh or 0.0
                income_acc = pay.income_wh_tax_account

                # if tti_report_type is "default" or blank -> show 0
                if not income_acc or income_acc.tti_report_type in ('default', False, ''):
                    income_tax = 0.0

                sheet.write_number(current_row, 7, income_tax, cell_format)

                # ===== COL 9 — Total Amount = Amount =====
                total_amount = (pay.amount or 0.0) + sale_tax + income_tax
                sheet.write_number(current_row, 8, total_amount, cell_format)

                # ===== COL 10 — Comments =====

                # Try to get linked invoice (payment → invoice)
                invoice = pay.reconciled_invoice_ids[:1]
                comment = ""

                if invoice:
                    residual = invoice.amount_residual
                    total = invoice.amount_total
                    if residual == 0:
                        comment = "Recovered"
                    elif 0 < residual < total:
                        comment = "Partially"
                    else:
                        comment = ""

                sheet.write(current_row, 9, comment, cell_format)
                current_row += 1

            # ===== SUBTOTAL ROW =====
            sheet.write(current_row, 4, "Subtotal:", subtotal_format)
            # Save this subtotal row index (Excel row number = current_row + 1)
            subtotal_rows.append(current_row + 1)

            # Excel rows are +1 because Excel is 1-indexed
            excel_end_row = current_row

            # F = Amount
            sheet.write_formula(current_row, 5, f"=SUM(F{excel_start_row}:F{excel_end_row})", subtotal_format)

            # G = Sale Tax (blank for now)
            sheet.write_formula(current_row, 6, f"=SUM(G{excel_start_row}:G{excel_end_row})", subtotal_format)

            # H = Invoice Tax (blank for now)
            sheet.write_formula(current_row, 7, f"=SUM(H{excel_start_row}:H{excel_end_row})", subtotal_format)

            # I = Total Amount
            sheet.write_formula(current_row, 8, f"=SUM(I{excel_start_row}:I{excel_end_row})", subtotal_format)

            current_row += 2  # blank row before next section

        # ===== GRAND TOTAL =====
        if subtotal_rows:
            sheet.write(current_row, 4, "Grand Total:", subtotal_format)

            amount_cells = ",".join(f"F{r}" for r in subtotal_rows)
            sale_cells = ",".join(f"G{r}" for r in subtotal_rows)
            income_cells = ",".join(f"H{r}" for r in subtotal_rows)
            total_cells = ",".join(f"I{r}" for r in subtotal_rows)

            # Amount
            sheet.write_formula(current_row, 5, f"=SUM({amount_cells})", subtotal_format)
            # Sale Tax
            sheet.write_formula(current_row, 6, f"=SUM({sale_cells})", subtotal_format)
            # Income Tax
            sheet.write_formula(current_row, 7, f"=SUM({income_cells})", subtotal_format)
            # Total Amount
            sheet.write_formula(current_row, 8, f"=SUM({total_cells})", subtotal_format)

            current_row += 2

        # ===== FINALIZE =====
        workbook.close()
        output.seek(0)

        file_data = output.read()
        attachment = self.env['ir.attachment'].create({
            'name': 'payment_recovery_report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self'
        }

