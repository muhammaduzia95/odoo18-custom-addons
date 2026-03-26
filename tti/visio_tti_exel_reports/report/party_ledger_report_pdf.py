from odoo import models
from collections import defaultdict


class PartyLedgerPDFReport(models.AbstractModel):
    _name = 'report.visio_tti_exel_reports.party_ledger_pdf_report'
    _description = 'Party Ledger PDF Report'

    def _calculate_amount_by_report_type(self, move_lines, report_types):
        """Same as Excel"""
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

    def _get_report_values(self, docids, data=None):
        wizard = self.env['tti.report.wizard'].browse(docids)
        partner = wizard.customer_id

        opening_balance = self._calculate_opening_balance(partner, wizard.date_from, wizard.state)

        # Main lines
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

        # Group by move_id
        lines_by_move = defaultdict(list)
        for line in journal_items:
            lines_by_move[line.move_id].append(line)

        # Group by date
        moves_by_date = defaultdict(lambda: {'invoices': [], 'entries': [], 'payments': []})

        for move_id, lines in lines_by_move.items():
            move_date = lines[0].date
            move_type = lines[0].move_type
            has_payment_lines = any(l.payment_id for l in lines)

            if move_type in ['out_invoice', 'out_refund']:
                moves_by_date[move_date]['invoices'].append((move_id, lines))
            elif move_type == 'entry' and has_payment_lines:
                moves_by_date[move_date]['payments'].append((move_id, lines))
            elif move_type == 'entry':
                moves_by_date[move_date]['entries'].append((move_id, lines))

        all_dates = sorted(moves_by_date.keys())

        lines = []
        balance = opening_balance
        sr = 1

        total_amount = total_gst = total_inv_total = 0.0
        total_cheque = total_sale_tax = total_income_tax = total_payment_total = 0.0

        for current_date in all_dates:
            # Invoices
            for move_id, move_lines in moves_by_date[current_date]['invoices']:
                so_list = move_id.invoice_line_ids.mapped('sale_line_ids.order_id')
                narration = ', '.join(filter(None, so_list.mapped('tti_pi_buyer.name')))
                source_doc = ', '.join(filter(None, so_list.mapped('tti_si_po')))
                so_names = ', '.join(so_list.mapped('name'))
                applicants = ', '.join(filter(None, so_list.mapped('tti_pi_applicant.name')))
                categories = ', '.join(filter(None, so_list.mapped('tti_si_category.name')))

                amount = self._calculate_amount_by_report_type(move_lines, ['sale'])
                gst = self._calculate_amount_by_report_type(move_lines, ['tax'])
                total = amount + gst
                balance += total

                lines.append({
                    'sr': sr,
                    'date': current_date.strftime('%d-%b-%Y'),
                    'narration': narration,
                    'source_doc': source_doc,
                    'voucher_type': 'Sale',
                    'so_names': so_names,
                    'invoice_name': move_id.name,
                    'applicants': applicants,
                    'categories': categories,
                    'amount': amount,
                    'gst': gst,
                    'total': total,
                    'chq_amount': '',
                    'sale_tax': '',
                    'income_tax': '',
                    'payment_total': '',
                    'status': dict(move_id._fields['payment_state'].selection).get(move_id.payment_state, ''),
                    'balance': balance,
                })

                total_amount += amount
                total_gst += gst
                total_inv_total += total
                sr += 1

            # JVs
            for move_id, move_lines in moves_by_date[current_date]['entries']:
                inv_amount = self._calculate_amount_by_report_type(move_lines, ['sale'])
                inv_gst = self._calculate_amount_by_report_type(move_lines, ['tax'])
                inv_total = inv_amount + inv_gst

                cheque_amount = self._calculate_amount_by_report_type(move_lines, ['bank'])
                sale_tax = self._calculate_amount_by_report_type(move_lines, ['wht_sale'])
                income_tax = self._calculate_amount_by_report_type(move_lines, ['wht_income'])
                payment_total = cheque_amount + sale_tax + income_tax

                net_effect = inv_total - payment_total
                balance += net_effect

                lines.append({
                    'sr': sr,
                    'date': current_date.strftime('%d-%b-%Y'),
                    'narration': move_id.ref or '',
                    'source_doc': move_id.name or '',
                    'voucher_type': 'JV',
                    'so_names': '',
                    'invoice_name': move_id.name,
                    'applicants': '',
                    'categories': '',
                    'amount': inv_amount,
                    'gst': inv_gst,
                    'total': inv_total,
                    'chq_amount': cheque_amount,
                    'sale_tax': sale_tax,
                    'income_tax': income_tax,
                    'payment_total': payment_total,
                    'status': '',
                    'balance': balance,
                })

                total_amount += inv_amount
                total_gst += inv_gst
                total_inv_total += inv_total
                total_cheque += cheque_amount
                total_sale_tax += sale_tax
                total_income_tax += income_tax
                total_payment_total += payment_total
                sr += 1

            # Payments
            for move_id, move_lines in moves_by_date[current_date]['payments']:
                payment_lines = [l for l in move_lines if l.tti_report_type in ['bank', 'wht_sale', 'wht_income']]
                payment_line_with_id = next((l for l in payment_lines if l.payment_id), None)
                payment_ref = payment_line_with_id.payment_id.memo if payment_line_with_id and payment_line_with_id.payment_id else ''
                cheque_no = payment_line_with_id.payment_id.cheque_no if payment_line_with_id and payment_line_with_id.payment_id else ''

                cheque_amount = self._calculate_amount_by_report_type(payment_lines, ['bank'])
                sale_tax = self._calculate_amount_by_report_type(payment_lines, ['wht_sale'])
                income_tax = self._calculate_amount_by_report_type(payment_lines, ['wht_income'])
                payment_total = cheque_amount + sale_tax + income_tax
                balance -= payment_total

                lines.append({
                    'sr': sr,
                    'date': current_date.strftime('%d-%b-%Y'),
                    'narration': payment_ref,
                    'source_doc': cheque_no,
                    'voucher_type': 'Receipt',
                    'so_names': '',
                    'invoice_name': '',
                    'applicants': '',
                    'categories': '',
                    'amount': '',
                    'gst': '',
                    'total': '',
                    'chq_amount': cheque_amount,
                    'sale_tax': sale_tax,
                    'income_tax': income_tax,
                    'payment_total': payment_total,
                    'status': '',
                    'balance': balance,
                })

                total_cheque += cheque_amount
                total_sale_tax += sale_tax
                total_income_tax += income_tax
                total_payment_total += payment_total
                sr += 1

        final_balance = opening_balance + total_inv_total - total_payment_total

        address_parts = [partner.street or '', partner.street2 or '', partner.city or '',
                         partner.state_id.name if partner.state_id else '',
                         partner.country_id.name if partner.country_id else '']
        full_address = ', '.join(part for part in address_parts if part)

        return {
            'doc_ids': docids,
            'doc_model': 'tti.report.wizard',
            'data': data,
            'docs': wizard,
            'company': self.env.company,
            'partner': partner,
            'full_address': full_address,
            'opening_balance': opening_balance,
            'lines': lines,
            'total_amount': total_amount,
            'total_gst': total_gst,
            'total_inv_total': total_inv_total,
            'total_cheque': total_cheque,
            'total_sale_tax': total_sale_tax,
            'total_income_tax': total_income_tax,
            'total_payment_total': total_payment_total,
            'final_balance': final_balance,
            'total_invoices': sum(len(moves_by_date[d]['invoices']) for d in all_dates),
        }
