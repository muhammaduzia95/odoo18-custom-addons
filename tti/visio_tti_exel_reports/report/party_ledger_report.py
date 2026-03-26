from odoo import models
from odoo.tools import date_utils
from odoo.tools.misc import xlsxwriter
import base64
import io
from datetime import date
from collections import defaultdict


class PartyLedgerExcelReport(models.AbstractModel):
    _name = 'report.visio_tti_exel_reports.party_ledger_report'
    _description = 'Party Ledger Excel Report'

    def _calculate_amount_by_report_type(self, move_lines, report_types):
        """Calculate amount for specific report types"""
        amount = 0.0
        for line in move_lines:
            if line.tti_report_type in report_types:
                if line.tti_report_type in ['sale', 'tax']:
                    amount += line.credit - line.debit
                elif line.tti_report_type in ['bank', 'wht_sale', 'wht_income']:
                    amount += line.debit - line.credit
        return amount

    def _calculate_opening_balance(self, partner, date_from, state):
        """Calculate opening balance using the same logic as main report"""
        # Get all journal items before the date_from
        opening_domain = [
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['entry', 'out_invoice', 'out_refund']),
            ('date', '<', date_from),
        ]
        if state == 'both':
            opening_domain += [('parent_state', 'in', ['draft', 'posted'])]
        elif state in ['draft', 'posted']:
            opening_domain += [('parent_state', '=', state)]

        opening_journal_items = self.env['account.move.line'].search(opening_domain, order='date asc, move_id asc')

        # Group lines by move_id and categorize (same as main report)
        lines_by_move = defaultdict(list)
        for line in opening_journal_items:
            lines_by_move[line.move_id].append(line)

        # Group moves by date and type (same as main report)
        moves_by_date = defaultdict(lambda: {'invoices': [], 'entries': [], 'payments': []})

        for move_id, lines in lines_by_move.items():
            move_date = lines[0].date
            move_type = lines[0].move_type

            # Check if this move has payment-related lines
            has_payment_lines = any(line.payment_id for line in lines)

            if move_type in ['out_invoice', 'out_refund']:
                moves_by_date[move_date]['invoices'].append((move_id, lines))
            elif move_type == 'entry' and has_payment_lines:
                moves_by_date[move_date]['payments'].append((move_id, lines))
            elif move_type == 'entry':
                moves_by_date[move_date]['entries'].append((move_id, lines))

        # Calculate opening balance following same logic as main report
        opening_balance = 0.0

        for current_date in sorted(moves_by_date.keys()):
            # Process Invoices
            for move_id, lines in moves_by_date[current_date]['invoices']:
                invoice_lines = [l for l in lines if l.tti_report_type in ['sale', 'tax']]
                amount = self._calculate_amount_by_report_type(invoice_lines, ['sale'])
                gst = self._calculate_amount_by_report_type(invoice_lines, ['tax'])
                total = amount + gst
                opening_balance += total

            # Process Journal Entries (JV)
            for move_id, lines in moves_by_date[current_date]['entries']:
                relevant_lines = [l for l in lines if
                                  l.tti_report_type in ['sale', 'tax', 'bank', 'wht_sale', 'wht_income']]

                # Calculate invoice amounts (sale + tax)
                inv_amount = self._calculate_amount_by_report_type(relevant_lines, ['sale'])
                inv_gst = self._calculate_amount_by_report_type(relevant_lines, ['tax'])
                inv_total = inv_amount + inv_gst

                # Calculate payment amounts
                cheque_amount = self._calculate_amount_by_report_type(relevant_lines, ['bank'])
                sale_tax = self._calculate_amount_by_report_type(relevant_lines, ['wht_sale'])
                income_tax = self._calculate_amount_by_report_type(relevant_lines, ['wht_income'])
                payment_total = cheque_amount + sale_tax + income_tax

                # Net effect on balance
                net_effect = inv_total - payment_total
                opening_balance += net_effect

            # Process Payment Entries
            for move_id, lines in moves_by_date[current_date]['payments']:
                payment_lines = [l for l in lines if l.tti_report_type in ['bank', 'wht_sale', 'wht_income']]

                # Calculate payment amounts
                cheque_amount = self._calculate_amount_by_report_type(payment_lines, ['bank'])
                sale_tax = self._calculate_amount_by_report_type(payment_lines, ['wht_sale'])
                income_tax = self._calculate_amount_by_report_type(payment_lines, ['wht_income'])
                payment_total = cheque_amount + sale_tax + income_tax

                opening_balance -= payment_total

        return opening_balance

    def _generate_excel(self, wizard):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Party Ledger')

        title_format = workbook.add_format({'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter'})
        data_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Arial', 'font_size': 10})
        header_format = workbook.add_format(
            {'bold': True, 'num_format': '#,##0.00', 'border': 1, 'align': 'center', 'valign': 'vcenter',
             'font_name': 'Arial', 'font_size': 10})
        src = workbook.add_format(
            {'border': 1, 'font_size': 10, 'align': 'center'})
        content_format = workbook.add_format(
            {'border': 1, 'font_size': 10, 'align': 'center', 'num_format': '#,##0.00'})
        info_label_format = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'left'})
        info_value_format = workbook.add_format({'font_size': 10, 'align': 'left'})

        company = self.env.company
        partner = wizard.customer_id
        state = wizard.state

        address_parts = [partner.street or '', partner.street2 or '', partner.city or '',
                         partner.state_id.name if partner.state_id else '',
                         partner.country_id.name if partner.country_id else '']
        full_address = ', '.join(part for part in address_parts if part)

        info_row = 2
        sheet.write(info_row, 2, company.name or '', info_value_format)
        sheet.write(info_row + 1, 2, company.street or '', info_value_format)
        sheet.write(info_row + 2, 2, 'NTN:', data_format)
        sheet.write(info_row + 2, 3, company.vat or '', info_value_format)
        sheet.write(info_row + 3, 2, 'Period:', data_format)
        sheet.write(info_row + 3, 3,
                    f"{wizard.date_from.strftime('%d-%b-%Y')} to {wizard.date_to.strftime('%d-%b-%Y')}",
                    info_value_format)

        sheet.write(info_row, 10, 'Client Name:', data_format)
        sheet.write(info_row, 11, partner.name or '', info_value_format)
        sheet.write(info_row + 1, 10, 'Address:', data_format)
        sheet.write(info_row + 1, 11, full_address, info_value_format)
        sheet.write(info_row + 2, 10, 'NTN:', data_format)
        sheet.write(info_row + 2, 11, partner.vat or '', info_value_format)

        sheet.merge_range('A1:P1', 'Customer Ledger', title_format)
        sheet.merge_range('J8:L8', 'Invoice', header_format)
        sheet.merge_range('M8:P8', 'Payment', header_format)

        headers = ['Sr #', 'Date', 'Narration', 'Source Document', 'Voucher Type', 'Sale order no', 'Invoice #',
                   'Applicant', 'Category', 'Amount', 'GST', 'Total', 'Chq amount', 'Sale Tax', 'Income Tax', 'Total',
                   'Status', 'Balance']
        column_widths = [4, 12, 14, 18, 12, 14, 14, 15, 12, 8, 12, 8, 12, 9, 11, 9, 12, 10]

        for col, width in enumerate(column_widths):
            sheet.set_column(col, col, width)

        for col, header in enumerate(headers):
            sheet.write(8, col, header, header_format)

        row = 9
        sr = 1

        # Calculate opening balance using the new method
        opening_balance = self._calculate_opening_balance(partner, wizard.date_from, wizard.state)

        sheet.merge_range(row, 0, row, 16, 'Opening', header_format)
        sheet.write(row, 17, opening_balance, header_format)
        row += 1

        balance = opening_balance

        domain = [
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['entry', 'out_invoice', 'out_refund']),
            ('date', '>=', wizard.date_from),
            ('date', '<=', wizard.date_to),
        ]
        if wizard.state == 'both':
            domain += [('parent_state', 'in', ['draft', 'posted'])]
        elif wizard.state in ['draft', 'posted']:
            domain += [('parent_state', '=', wizard.state)]

        journal_items = self.env['account.move.line'].search(domain, order='date asc, move_id asc')

        # Group lines by move_id and categorize
        lines_by_move = defaultdict(list)
        for line in journal_items:
            lines_by_move[line.move_id].append(line)

        # Group moves by date and type
        moves_by_date = defaultdict(lambda: {'invoices': [], 'entries': [], 'payments': []})

        for move_id, lines in lines_by_move.items():
            move_date = lines[0].date
            move_type = lines[0].move_type

            # Check if this move has payment-related lines
            has_payment_lines = any(line.payment_id for line in lines)

            if move_type in ['out_invoice', 'out_refund']:
                moves_by_date[move_date]['invoices'].append((move_id, lines))
            elif move_type == 'entry' and has_payment_lines:
                moves_by_date[move_date]['payments'].append((move_id, lines))
            elif move_type == 'entry':
                moves_by_date[move_date]['entries'].append((move_id, lines))

        all_dates = sorted(moves_by_date.keys())

        total_amount = total_gst = total_inv_total = 0.0
        total_cheque = total_sale_tax = total_income_tax = total_payment_total = 0.0

        for current_date in all_dates:
            # Process Invoices first
            for move_id, lines in moves_by_date[current_date]['invoices']:
                # Get invoice-related lines only
                invoice_lines = [l for l in lines if l.tti_report_type in ['sale', 'tax']]

                # Get related sale order info from move_id
                so_list = move_id.invoice_line_ids.mapped('sale_line_ids.order_id')
                narration = ', '.join(filter(None, so_list.mapped('tti_pi_buyer.name')))
                source_doc = ', '.join(filter(None, so_list.mapped('tti_si_po')))
                so_names = ', '.join(so_list.mapped('name'))
                applicants = ', '.join(filter(None, so_list.mapped('tti_pi_applicant.name')))
                categories = ', '.join(filter(None, so_list.mapped('tti_si_category.name')))

                # Calculate amounts using tti_report_type
                amount = self._calculate_amount_by_report_type(invoice_lines, ['sale'])
                gst = self._calculate_amount_by_report_type(invoice_lines, ['tax'])
                total = amount + gst
                balance += total

                values = [sr, current_date.strftime('%d-%b-%Y'), narration, source_doc, 'Sale', so_names,
                          move_id.name, applicants, categories, amount, gst, total, '', '', '', '',
                          dict(move_id._fields['payment_state'].selection).get(move_id.payment_state, ''),
                          balance]

                for col, val in enumerate(values):
                    if col == 0:
                        sheet.write(row, col, val, src)
                    else:
                        sheet.write(row, col, val, content_format)

                row += 1
                sr += 1

                total_amount += amount
                total_gst += gst
                total_inv_total += total

            # Process Journal Entries (JV)
            for move_id, lines in moves_by_date[current_date]['entries']:
                # Filter lines by report type
                relevant_lines = [l for l in lines if
                                  l.tti_report_type in ['sale', 'tax', 'bank', 'wht_sale', 'wht_income']]

                # Calculate invoice amounts (sale + tax)
                inv_amount = self._calculate_amount_by_report_type(relevant_lines, ['sale'])
                inv_gst = self._calculate_amount_by_report_type(relevant_lines, ['tax'])
                inv_total = inv_amount + inv_gst

                # Calculate payment amounts
                cheque_amount = self._calculate_amount_by_report_type(relevant_lines, ['bank'])
                sale_tax = self._calculate_amount_by_report_type(relevant_lines, ['wht_sale'])
                income_tax = self._calculate_amount_by_report_type(relevant_lines, ['wht_income'])
                payment_total = cheque_amount + sale_tax + income_tax

                # Net effect on balance
                net_effect = inv_total - payment_total
                balance += net_effect

                values = [sr, current_date.strftime('%d-%b-%Y'), move_id.ref or '', move_id.name or '', 'JV', '',
                          move_id.name, '', '', inv_amount, inv_gst, inv_total, cheque_amount, sale_tax, income_tax,
                          payment_total,
                          '', balance]

                for col, val in enumerate(values):
                    if col == 0:
                        sheet.write(row, col, val, src)
                    else:
                        sheet.write(row, col, val, content_format)

                row += 1
                sr += 1

                total_amount += inv_amount
                total_gst += inv_gst
                total_inv_total += inv_total
                total_cheque += cheque_amount
                total_sale_tax += sale_tax
                total_income_tax += income_tax
                total_payment_total += payment_total

            # Process Payment Entries
            for move_id, lines in moves_by_date[current_date]['payments']:
                # Filter payment-related lines only
                payment_lines = [l for l in lines if l.tti_report_type in ['bank', 'wht_sale', 'wht_income']]

                # Get payment reference from the payment_id
                payment_ref = ''
                cheque_no = ''
                payment_line_with_id = next((l for l in lines if l.payment_id), None)
                if payment_line_with_id and payment_line_with_id.payment_id:
                    payment_obj = payment_line_with_id.payment_id
                    payment_ref = payment_obj.memo or ''
                    cheque_no = payment_obj.cheque_no or ''

                # Calculate payment amounts
                cheque_amount = self._calculate_amount_by_report_type(payment_lines, ['bank'])
                sale_tax = self._calculate_amount_by_report_type(payment_lines, ['wht_sale'])
                income_tax = self._calculate_amount_by_report_type(payment_lines, ['wht_income'])
                payment_total = cheque_amount + sale_tax + income_tax

                balance -= payment_total

                values = [sr, current_date.strftime('%d-%b-%Y'), payment_ref, cheque_no, 'Receipt', '',
                          '', '', '', '', '', '', cheque_amount, sale_tax, income_tax, payment_total,
                          '', balance]

                for col, val in enumerate(values):
                    if col == 0:
                        sheet.write(row, col, val, src)
                    else:
                        sheet.write(row, col, val, content_format)

                total_cheque += cheque_amount
                total_sale_tax += sale_tax
                total_income_tax += income_tax
                total_payment_total += payment_total

                row += 1
                sr += 1

        final_balance = opening_balance + total_inv_total - total_payment_total

        totals_label_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'font_size': 10})
        totals_value_format = workbook.add_format(
            {'bold': True, 'border': 1, 'align': 'center', 'font_size': 10, 'num_format': '#,##0.00'})

        sheet.merge_range(row, 0, row, 8, 'TOTAL', totals_label_format)
        sheet.write(row, 9, total_amount, totals_value_format)
        sheet.write(row, 10, total_gst, totals_value_format)
        sheet.write(row, 11, total_inv_total, totals_value_format)
        sheet.write(row, 12, total_cheque, totals_value_format)
        sheet.write(row, 13, total_sale_tax, totals_value_format)
        sheet.write(row, 14, total_income_tax, totals_value_format)
        sheet.write(row, 15, total_payment_total, totals_value_format)
        sheet.write(row, 16, '', totals_value_format)
        sheet.write(row, 17, final_balance, totals_value_format)

        summary_label_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
        })

        summary_value_format = workbook.add_format({
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00'
        })
        row += 4
        summary_col_start = 14

        total_invoice_count = len([item for date_moves in moves_by_date.values()
                                   for item in date_moves['invoices']])

        summary_data = [
            ('Total Invoices:', total_invoice_count),
            ('Total Invoice Amount:', total_inv_total),
            ('Total Recovery:', total_payment_total),
            ('Balance:', final_balance),
        ]

        for idx, (label, value) in enumerate(summary_data):
            summary_row = row + idx
            sheet.merge_range(summary_row, summary_col_start, summary_row, summary_col_start + 1, label,
                              summary_label_format)
            sheet.merge_range(summary_row, summary_col_start + 2, summary_row, summary_col_start + 3, value,
                              summary_value_format)

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        filename = f"Party_Ledger_Report_{date.today().strftime('%Y%m%d')}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': 'tti.report.wizard',
            'res_id': wizard.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }