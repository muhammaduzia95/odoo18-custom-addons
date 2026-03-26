# tti\visio_tti_exel_reports\wizard\recovery_report.py
# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import base64
import xlsxwriter


class RecoveryReportWizard(models.TransientModel):
    _name = 'recovery.report.wizard'
    _description = 'Recovery Report Wizard'

    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")

    holding_tax = fields.Float(string="Income WHT (%)", default=6.0,)
    commission = fields.Float(string="Commission (%)", default=12.0, readonly=True)

    def action_print_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Recovery Report')

        # Formats
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14})
        subtitle_fmt = workbook.add_format({'bold': True, 'font_size': 12})
        bold_fmt = workbook.add_format({'bold': True})
        header_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        cell_fmt = workbook.add_format({'border': 1})
        amount_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        amount_format_neg = workbook.add_format({'border': 1, 'num_format': '#,##0.00;(#,##0.00)'})
        total_fmt = workbook.add_format({'bottom': 1, 'bold': True, 'num_format': '#,##0.00'})
        total_fmt_neg = workbook.add_format({'bottom': 1, 'bold': True, 'num_format': '#,##0.00;(#,##0.00)'})

        # Dates
        from_str = self.date_from.strftime('%d-%b-%y') if self.date_from else ''
        to_str = self.date_to.strftime('%d-%b-%y') if self.date_to else ''
        print("Date From:", self.date_from, "| Date To:", self.date_to)

        # Header block
        worksheet.write(0, 0, 'Textile Testing International', title_fmt)
        worksheet.write(1, 0, 'Recovery Report - Eurofins', subtitle_fmt)
        worksheet.write(2, 0, 'Period from:', bold_fmt)
        worksheet.write(2, 1, from_str)
        worksheet.write(3, 0, 'Period to:', bold_fmt)
        worksheet.write(3, 1, to_str)

        # Table header
        headers = [
            'Reference No', 'Sales Tax Invoice #', 'Buyer Name', 'Customer',
            'Invoice Date', 'Recovery Date', 'Amount', 'Sales Tax',
            'Income Tax Withholding', 'Billable Amount', 'Recovered Amount',
            'Pending Recovery', 'Commission (%)', 'Commission (Amount)',
            'Recovery Status'
        ]
        start_row = 5
        for col, title in enumerate(headers):
            worksheet.write(start_row, col, title, header_fmt)

        worksheet.set_row(start_row, 22)
        worksheet.set_column(0, 0, 16)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 3, 22)
        worksheet.set_column(4, 5, 14)
        worksheet.set_column(6, 11, 16)
        worksheet.set_column(12, 13, 16)
        worksheet.set_column(14, 14, 18)

        # ===== Data building =====
        domain = [('state', 'in', ['paid', 'in_process', 'check'])]
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))

        print("Payment domain:", domain)
        payments = self.env['account.payment'].sudo().search(domain)
        print(f"Payments found: {len(payments)}")

        # Show the selection keys once (to confirm 'mts' is correct)
        try:
            sel = dict(self.env['sale.order']._fields['tti_si_select_partner'].selection(self.env['sale.order']))
            print("tti_si_select_partner selection keys:", list(sel.keys()))
        except Exception as e:
            print("Could not read selection keys for tti_si_select_partner:", e)

        # collect invoices linked to those payments + build payment-date & recovered maps per invoice
        invoice_ids = set()
        inv_to_paydates = {}  # {inv_id: [dates]}
        inv_to_recovered = {}  # {inv_id: total recovered in company currency}
        print("Scanning payments → invoices...")
        for idx, p in enumerate(payments, start=1):
            if idx in (5, 6):
                print(
                    f"[PAYMENT #{idx}] {p.name} | State={p.state} | Date={p.date} | Amount={p.amount} | Partner={p.partner_id.display_name}")

            linked_rs = getattr(p, 'reconciled_invoice_ids', None) or self.env['account.move'].browse()
            linked = linked_rs.filtered(
                lambda m: m.move_type == 'out_invoice' and m.state == 'posted') if linked_rs else self.env[
                'account.move'].browse()

            if idx in (5, 6):
                print(f"  reconciled_invoice_ids count: {len(linked)}")

            for inv in linked:
                invoice_ids.add(inv.id)
                if inv.id not in inv_to_paydates:
                    inv_to_paydates[inv.id] = []
                if p.date:
                    inv_to_paydates[inv.id].append(p.date)
                if inv.id not in inv_to_recovered:
                    inv_to_recovered[inv.id] = 0.0
                if idx in (5, 6):
                    print(f"    + Linked Invoice: {inv.name} (id={inv.id}) | add payment date {p.date}")

            # add precise recovered amounts via partial reconciles on receivable lines
            receivable_lines = p.move_id.line_ids.filtered(
                lambda l: getattr(l.account_id, 'account_type', '') == 'asset_receivable')
            if idx in (5, 6):
                print(f"  receivable lines: {len(receivable_lines)}")
            for rl in receivable_lines:
                partials = rl.matched_debit_ids | rl.matched_credit_ids
                for pr in partials:
                    mv_a = pr.debit_move_id.move_id
                    mv_b = pr.credit_move_id.move_id
                    target = mv_a if mv_a.move_type == 'out_invoice' else (
                        mv_b if mv_b.move_type == 'out_invoice' else False)
                    if target and target.state == 'posted':
                        invoice_ids.add(target.id)
                        # inv_to_recovered[target.id] = inv_to_recovered.get(target.id, 0.0) + pr.amount  # company currency
                        # convert PR amount from company currency -> PKR (per payment date)
                        try:
                            to_currency = self.env.ref('base.PKR')
                        except Exception:
                            to_currency = target.company_id.currency_id  # fallback (no-op if PKR missing)

                        company_curr = target.company_id.currency_id
                        rate_date = p.date or fields.Date.context_today(self)
                        amount_pkr = company_curr._convert(pr.amount, to_currency, target.company_id, rate_date)
                        inv_to_recovered[target.id] = inv_to_recovered.get(target.id, 0.0) + amount_pkr

                        if idx in (5, 6):
                            print(
                                f"    + PR to {target.name}: {pr.amount} {company_curr.name} -> {round(amount_pkr, 2)} PKR on {rate_date} (total now {round(inv_to_recovered[target.id], 2)} PKR)")

        invoices = self.env['account.move'].sudo().browse(list(invoice_ids))
        print(f"Unique sales invoices collected: {len(invoices)}")

        row = start_row + 1
        seen_pairs = set()
        so_hits = 0
        so_fallback_hits = 0
        mts_hits = 0
        non_mts_hits = 0

        total_amount_sum = 0.0
        total_sales_tax_sum = 0.0
        total_income_wh_sum = 0.0
        total_billable_sum = 0.0
        total_recovered_sum = 0.0
        total_commission_amt_sum = 0.0

        print("Scanning invoices → sale orders...")
        for idx, inv in enumerate(invoices, start=1):
            sale_orders = inv.invoice_line_ids.mapped('sale_line_ids.order_id')

            if idx in (5, 6):
                so_names_raw = [so.name for so in sale_orders]
                print(f"[INVOICE #{idx}] {inv.name} | SOs via lines count={len(sale_orders)} -> {so_names_raw}")

            if not sale_orders and inv.invoice_origin:
                origin_names = [x.strip() for x in inv.invoice_origin.replace(';', ',').split(',') if x.strip()]
                if origin_names:
                    so_fallback = self.env['sale.order'].sudo().search([('name', 'in', origin_names)])
                    if so_fallback:
                        sale_orders = so_fallback
                        so_fallback_hits += len(so_fallback)
                        if idx in (5, 6):
                            print(
                                f"  Fallback hits via invoice_origin={inv.invoice_origin}: {[s.name for s in so_fallback]}")

            if idx in (5, 6):
                for so in sale_orders:
                    print(f"    SO {so.name} | tti_si_select_partner(raw)={repr(so.tti_si_select_partner)}")

            sale_orders = sale_orders.filtered(lambda so: so.tti_si_select_partner == 'mts')

            if not sale_orders:
                non_mts_hits += 1
                if idx in (5, 6):
                    print(f"  Skipped {inv.name}: no SO with tti_si_select_partner='mts'")
                continue

            # pre-format invoice & recovery dates as strings (keep consistent with your header style)
            inv_date_str = inv.invoice_date.strftime('%d-%b-%y') if inv.invoice_date else ''
            pay_dates = inv_to_paydates.get(inv.id, [])
            rec_date = max(pay_dates) if pay_dates else None  # choose latest payment date
            rec_date_str = rec_date.strftime('%d-%b-%y') if rec_date else ''

            for so in sale_orders:
                mts_hits += 1
                key = (so.name or '', inv.name or '')
                if key in seen_pairs:
                    if idx in (5, 6):
                        print(f"    Duplicate pair skipped: {key}")
                    continue
                seen_pairs.add(key)
                so_hits += 1

                # --- Amount (SO untaxed − total charges), convert to PKR if needed ---
                amount = (so.amount_untaxed or 0.0) - (getattr(so, 'tti_total_charges', 0.0) or 0.0)
                # if getattr(so, 'currency_id', False) and so.currency_id.name != 'PKR':
                #     date_conv = so.date_order or fields.Date.context_today(self)
                #     try:
                #         rate = so.currency_id._convert(1.0, self.env.ref('base.PKR'), so.company_id, date_conv)
                #         amount *= rate
                #         if idx in (5, 6):
                #             print(f"      Amount FX -> rate={rate} on {date_conv}")
                #     except Exception as e:
                #         if idx in (5, 6):
                #             print("      Amount FX convert failed:", e)

                # convert SO/invoice currency -> PKR (like your other report)
                src_curr = getattr(so, 'currency_id', False) or inv.currency_id
                if src_curr and src_curr.name != 'PKR':
                    try:
                        to_currency = self.env.ref('base.PKR')
                    except Exception:
                        to_currency = inv.company_id.currency_id  # fallback

                    date_conv = so.date_order or inv.invoice_date or fields.Date.context_today(self)
                    try:
                        amount = src_curr._convert(amount, to_currency, inv.company_id, date_conv)
                        if idx in (5, 6):
                            print(f"      Amount FX: {src_curr.name} -> PKR on {date_conv} | amt={round(amount, 2)}")
                    except Exception as e:
                        if idx in (5, 6):
                            print("      Amount FX convert failed:", e)

                # --- Sales Tax = Amount * (sum of partner.sales_taxes.percent) ---
                partner = so.partner_id
                taxes_rs = partner.sales_taxes or self.env['account.tax']
                percent_only = taxes_rs.filtered(lambda t: getattr(t, 'amount_type', '') == 'percent')
                tax_rate = sum(t.amount for t in percent_only)
                sales_tax = (amount * tax_rate / 100.0) if tax_rate else 0.0

                # --- Income Tax Withholding = -(Amount + Sales Tax) * holding_tax% ---
                income_tax_withholding = -((amount + sales_tax) * (self.holding_tax / 100.0))
                income_tax_withholding_abs = abs(income_tax_withholding)  # For billable amount calc

                # --- Billable Amount = Amount + Income Tax Withholding (positive value) ---
                billable_amount = amount - income_tax_withholding_abs

                if idx in (5, 6):
                    print(f"      IncomeTaxWH={round(income_tax_withholding, 2)} (HoldingTax%={self.holding_tax})")

                # --- Write columns ---
                # 0: Reference No (SO)
                worksheet.write(row, 0, so.name or '', cell_fmt)
                # 1: Sales Tax Invoice #
                worksheet.write(row, 1, inv.name or '', cell_fmt)
                # 2: Buyer Name (handle Char or M2O)
                buyer_val = getattr(so.tti_pi_buyer, 'display_name', False) if hasattr(so, 'tti_pi_buyer') else False
                if not buyer_val:
                    buyer_val = so.tti_pi_buyer if hasattr(so, 'tti_pi_buyer') else ''
                worksheet.write(row, 2, buyer_val or '', cell_fmt)
                # 3: Customer (SO partner)
                worksheet.write(row, 3, so.partner_id.name or '', cell_fmt)
                # 4: Invoice Date
                worksheet.write(row, 4, inv_date_str, cell_fmt)
                # 5: Recovery Date (latest linked payment date in range)
                worksheet.write(row, 5, rec_date_str, cell_fmt)
                # 6: Amount
                worksheet.write_number(row, 6, round(amount, 2), amount_format)
                # 7: Sales Tax
                worksheet.write_number(row, 7, round(sales_tax, 2), amount_format)
                # 8: Income Tax WithHolding
                worksheet.write_number(row, 8, income_tax_withholding, amount_format_neg)
                worksheet.write_number(row, 9, round(billable_amount, 2), amount_format)

                # 10: Recovered Amount (cap to Billable Amount)
                recovered_raw = round(inv_to_recovered.get(inv.id, 0.0), 2)
                recovered_capped = min(recovered_raw, round(billable_amount, 2))
                worksheet.write_number(row, 10, recovered_capped, amount_format)

                # 11: Pending Recovery = Billable - Recovered (never negative)
                pending_recovery_raw = billable_amount - recovered_capped
                pending_recovery = round(pending_recovery_raw if pending_recovery_raw > 0 else 0.0, 2)
                worksheet.write_number(row, 11, pending_recovery, amount_format)

                # 12: Commission (%) = wizard field (as a number, e.g. 12.0)
                worksheet.write_number(row, 12, float(self.commission or 0.0), cell_fmt)

                # 13: Commission (Amount) = Recovered * commission%
                commission_amount = recovered_capped * (float(self.commission or 0.0) / 100.0)
                worksheet.write_number(row, 13, round(commission_amount, 2), amount_format)

                # 14: Recovery Status (Paid if pending == 0 else Partial)
                status = 'Paid' if round(pending_recovery, 2) == 0.0 else 'Partial'
                worksheet.write(row, 14, status, cell_fmt)

                if idx in (5, 6):
                    print(
                        f"      Pending={pending_recovery} | Comm%={self.commission} | CommAmt={round(commission_amount, 2)} | Status={status}")

                row += 1

        # ---- Totals row (recompute in Python; no Excel formulas) ----
        tot_amount = tot_sales_tax = tot_income_wh = tot_billable = tot_recovered = tot_commission = 0.0
        seen_pairs_tot = set()

        for inv in invoices:
            # find SOs like you did when writing rows (via lines + fallback by origin)
            sos = inv.invoice_line_ids.mapped('sale_line_ids.order_id')
            if not sos and inv.invoice_origin:
                names = [x.strip() for x in inv.invoice_origin.replace(';', ',').split(',') if x.strip()]
                if names:
                    sos = self.env['sale.order'].sudo().search([('name', 'in', names)])

            sos = sos.filtered(lambda so: so.tti_si_select_partner == 'mts')

            # latest linked payment date was only for display, totals don't need it
            for so in sos:
                key = (so.name or '', inv.name or '')
                if key in seen_pairs_tot:
                    continue
                seen_pairs_tot.add(key)

                # Amount = SO untaxed − total charges (convert to PKR like in rows)
                amount = (so.amount_untaxed or 0.0) - (getattr(so, 'tti_total_charges', 0.0) or 0.0)
                src_curr = getattr(so, 'currency_id', False) or inv.currency_id
                if src_curr and src_curr.name != 'PKR':
                    try:
                        to_curr = self.env.ref('base.PKR')
                    except Exception:
                        to_curr = inv.company_id.currency_id
                    date_conv = so.date_order or inv.invoice_date or fields.Date.context_today(self)
                    try:
                        amount = src_curr._convert(amount, to_curr, inv.company_id, date_conv)
                    except Exception:
                        pass

                # Sales Tax from partner percent taxes
                partner = so.partner_id
                taxes_rs = partner.sales_taxes or self.env['account.tax']
                percent_only = taxes_rs.filtered(lambda t: getattr(t, 'amount_type', '') == 'percent')
                tax_rate = sum(t.amount for t in percent_only)
                sales_tax = (amount * tax_rate / 100.0) if tax_rate else 0.0

                # Income Tax Withholding and Billable
                income_wh = -((amount + sales_tax) * (self.holding_tax / 100.0))
                billable = amount + abs(income_wh)

                # Recovered (cap to billable, like in rows)
                recovered_raw = round(inv_to_recovered.get(inv.id, 0.0), 2)
                recovered = min(recovered_raw, round(billable, 2))

                # Commission (on recovered)
                commission_amt = recovered * (float(self.commission or 0.0) / 100.0)

                # accumulate
                tot_amount += amount
                tot_sales_tax += sales_tax
                tot_income_wh += income_wh
                tot_billable += billable
                tot_recovered += recovered
                tot_commission += commission_amt

        # write totals to the same columns you used above
        tot_row = row
        worksheet.write_number(tot_row, 6, round(tot_amount, 2), total_fmt)  # G Amount
        worksheet.write_number(tot_row, 7, round(tot_sales_tax, 2), total_fmt)  # H Sales Tax
        worksheet.write_number(tot_row, 8, round(tot_income_wh, 2), total_fmt_neg)  # I Income Tax WH (neg style)
        worksheet.write(tot_row, 9, '', total_fmt)  # J Billable Amount
        worksheet.write_number(tot_row, 10, round(tot_recovered, 2), total_fmt)  # K Recovered
        worksheet.write_number(tot_row, 13, round(tot_commission, 2), total_fmt)  # N Commission Amt

        print(
            f"Totals → Amount={round(total_amount_sum, 2)}, SalesTax={round(total_sales_tax_sum, 2)}, "
            f"IncomeWH={round(total_income_wh_sum, 2)}, Billable={round(total_billable_sum, 2)}, "
            f"Recovered={round(total_recovered_sum, 2)}, CommissionAmt={round(total_commission_amt_sum, 2)}"
        )

        workbook.close()
        output.seek(0)
        file_data = output.read()

        attachment = self.env['ir.attachment'].create({
            'name': 'recovery_report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        print(f"Report generated with {row - (start_row + 1)} data rows.")

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
