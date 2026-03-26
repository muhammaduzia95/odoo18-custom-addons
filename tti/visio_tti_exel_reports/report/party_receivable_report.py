from odoo import models
import io
import base64
import xlsxwriter


class PartyReceivableReport(models.AbstractModel):
    _name = 'report.visio_tti_exel_reports.party_receivable_report'
    _description = 'Party Receivable Excel Generator'

    def _calculate_opening_balance(self, wizard, partner_ids):
        """
        Calculate the opening balance for each partner based on closing balance
        of the previous period (before the start date)
        """
        opening_domain = [
            ('date', '<', wizard.date_from),
            ('partner_id', 'in', partner_ids),
        ]

        if wizard.state == 'both':
            opening_domain += [('parent_state', 'in', ['draft', 'posted'])]
        elif wizard.state in ['draft', 'posted']:
            opening_domain += [('parent_state', '=', wizard.state)]
        if wizard.city_zone_ids:
            opening_domain += [('partner_id.tti_city_zone_id', 'in', wizard.city_zone_ids.ids)]
        if wizard.category_ids:
            opening_domain += ['|',
                               ('move_id.tti_si_category_ids', 'in', wizard.category_ids.ids),
                               ('payment_id.tti_si_category_ids', 'in', wizard.category_ids.ids)
                               ]
        opening_items = self.env['account.move.line'].search(opening_domain)

        # Initialize opening balances
        opening_balances = {partner_id: 0.0 for partner_id in partner_ids}

        # Calculate opening balance by processing all transactions before start date
        for item in opening_items:
            partner_id = item.partner_id.id
            if partner_id not in opening_balances:
                continue

            # Calculate the net effect based on transaction type
            if item.tti_report_type == 'receivable':
                # Receivable increases the balance (debit - credit)
                opening_balances[partner_id] += (item.debit - item.credit)

            elif item.tti_report_type == 'sale':
                # Sales increase the balance (credit - debit becomes positive receivable)
                opening_balances[partner_id] += (item.credit - item.debit)

            elif item.tti_report_type == 'tax':
                # Tax amounts increase the balance
                opening_balances[partner_id] += (item.credit - item.debit)

            elif item.tti_report_type == 'bank':
                # Bank payments reduce the balance (debit - credit becomes negative)
                opening_balances[partner_id] -= (item.debit - item.credit)

            elif item.tti_report_type == 'wht_sale':
                # Withholding tax reduces the balance
                opening_balances[partner_id] -= (item.debit - item.credit)

            elif item.tti_report_type == 'wht_income':
                # Income tax withholding reduces the balance
                opening_balances[partner_id] -= (item.debit - item.credit)

        return opening_balances

    def _generate_excel(self, wizard):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Party Receivable")

        bold = workbook.add_format({'bold': True})
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        table_label_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 10,
            'font_name': 'Arial'
        })

        table_value_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'center',
            'font_size': 10,
            'font_name': 'Arial'
        })

        label_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'font_size': 10,
            'font_name': 'Arial'
        })

        value_format = workbook.add_format({
            'align': 'left',
            'font_size': 10,
            'font_name': 'Arial'
        })
        total_format = workbook.add_format({
            'num_format': '#,##0.00',
            'bold': True,
            'font_name': 'Arial',
            'align': 'center',
            'font_size': 10
        })

        worksheet.set_column('A:A', 15)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 15)

        if wizard.tax_filter == 'with_tax':
            worksheet.merge_range('A1:K1', 'Party Receivable Report', title_format)
        else:
            worksheet.merge_range('A1:I1', 'Party Receivable Report', title_format)

        start_row = 2
        col = 0
        worksheet.write(start_row, col, 'Zone', table_label_format)
        col += 1
        worksheet.write(start_row, col, 'Category', table_label_format)
        col += 1
        worksheet.write(start_row, col, 'Code', table_label_format)
        col += 1
        worksheet.write(start_row, col, 'Partner Name', table_label_format)
        col += 1
        worksheet.write(start_row, col, 'Opening', table_label_format)
        col += 1
        worksheet.write(start_row, col, 'Receivable', table_label_format)
        col += 1
        worksheet.write(start_row, col, 'Sales', table_label_format)
        col += 1
        worksheet.write(start_row, col, 'Recovery', table_label_format)
        col += 1

        if wizard.tax_filter == 'with_tax':
            worksheet.write(start_row, col, 'Sale Tax WH', table_label_format)
            col += 1
            worksheet.write(start_row, col, 'Income Tax WH', table_label_format)
            col += 1

        worksheet.write(start_row, col, 'Closing', table_label_format)

        domain = [
            ('date', '>=', wizard.date_from),
            ('date', '<=', wizard.date_to),
        ]

        if wizard.state == 'both':
            domain += [('parent_state', 'in', ['draft', 'posted'])]
        elif wizard.state in ['draft', 'posted']:
            domain += [('parent_state', '=', wizard.state)]
        if wizard.city_zone_ids:
            domain += [('partner_id.tti_city_zone_id', 'in', wizard.city_zone_ids.ids)]
        if wizard.category_ids:
            domain += [('move_id.tti_si_category_ids', 'in', wizard.category_ids.ids)]

        journal_items = self.env['account.move.line'].search(domain)
        current_period_partners = journal_items.mapped('partner_id')

        # Get all partners who had transactions before the start date
        opening_domain = [
            ('date', '<', wizard.date_from),
        ]
        if wizard.state == 'both':
            opening_domain += [('parent_state', 'in', ['draft', 'posted'])]
        elif wizard.state in ['draft', 'posted']:
            opening_domain += [('parent_state', '=', wizard.state)]
        if wizard.city_zone_ids:
            opening_domain += [('partner_id.tti_city_zone_id', 'in', wizard.city_zone_ids.ids)]
        if wizard.category_ids:
            opening_domain += [('move_id.tti_si_category_ids', 'in', wizard.category_ids.ids)]

        opening_items = self.env['account.move.line'].search(opening_domain)
        opening_partners = opening_items.mapped('partner_id')

        # Combine all partners
        all_partners = current_period_partners | opening_partners

        # Filter only customers
        customer_partners = all_partners.filtered(lambda p: p.customer_rank > 0)

        # Calculate opening balances using the separate function
        opening_balances = self._calculate_opening_balance(wizard, customer_partners.ids)

        # Create partner data map
        partner_data_map = {partner.id: {
            'partner': partner,
            'opening': opening_balances.get(partner.id, 0.0),
            'receivable': 0.0,
            'sales': 0.0,
            'recovery': 0.0,
            'sale_tax_wh': 0.0,
            'income_tax_wh': 0.0,
        } for partner in customer_partners}

        # Process current period transactions
        for item in journal_items:
            partner_id = item.partner_id.id
            if partner_id not in partner_data_map:
                continue

            if item.tti_report_type == 'receivable':
                partner_data_map[partner_id]['receivable'] += (item.debit - item.credit)

            elif item.tti_report_type == 'sale':
                partner_data_map[partner_id]['sales'] += (item.credit - item.debit)

            elif item.tti_report_type == 'tax' and wizard.tax_filter == 'with_tax':
                partner_data_map[partner_id]['sales'] += (item.credit - item.debit)

            elif item.tti_report_type == 'bank':
                partner_data_map[partner_id]['recovery'] += (item.debit - item.credit)

            elif item.tti_report_type == 'wht_sale':
                partner_data_map[partner_id]['sale_tax_wh'] += (item.debit - item.credit)

            elif item.tti_report_type == 'wht_income':
                partner_data_map[partner_id]['income_tax_wh'] += (item.debit - item.credit)

        invoices = journal_items.filtered(lambda x: x.move_type == 'out_invoice')

        total_opening = total_receivable = total_sales = total_recovery = 0.0
        total_sale_tax_wh = total_income_tax_wh = total_closing = 0.0

        row = start_row + 1
        for data in partner_data_map.values():
            partner = data['partner']
            opening = data['opening']
            receivable = data['receivable']
            sales = data['sales']
            recovery = data['recovery']
            sale_tax_wh = data['sale_tax_wh']
            income_tax_wh = data['income_tax_wh']

            if wizard.tax_filter == 'with_tax':
                closing = opening + sales - recovery - sale_tax_wh - income_tax_wh
            else:
                closing = opening + sales - recovery

            col = 0
            zone = partner.tti_city_zone_id.name if partner.tti_city_zone_id else ''
            worksheet.write(row, col, zone, table_value_format)
            col += 1

            partner_invoices = invoices.filtered(lambda inv: inv.partner_id.id == partner.id)
            categories = ', '.join(
                set(cat.name for inv in partner_invoices for cat in inv.move_id.tti_si_category_ids)) or ''
            worksheet.write(row, col, categories, table_value_format)
            col += 1

            worksheet.write(row, col, partner.code or '', table_value_format)
            col += 1
            worksheet.write(row, col, partner.name or '', table_value_format)
            col += 1
            worksheet.write(row, col, round(opening, 2), table_value_format)
            col += 1
            worksheet.write(row, col, round(receivable, 2), table_value_format)
            col += 1
            worksheet.write(row, col, round(sales, 2), table_value_format)
            col += 1
            worksheet.write(row, col, round(recovery, 2), table_value_format)
            col += 1

            if wizard.tax_filter == 'with_tax':
                worksheet.write(row, col, round(sale_tax_wh, 2), table_value_format)
                col += 1
                worksheet.write(row, col, round(income_tax_wh, 2), table_value_format)
                col += 1

            worksheet.write(row, col, round(closing, 2), table_value_format)
            row += 1

            total_opening += opening
            total_receivable += receivable
            total_sales += sales
            total_recovery += recovery
            total_closing += closing
            if wizard.tax_filter == 'with_tax':
                total_sale_tax_wh += sale_tax_wh
                total_income_tax_wh += income_tax_wh

        col = 0
        worksheet.write(row, col, '', total_format)
        col += 1
        worksheet.write(row, col, '', total_format)
        col += 1
        worksheet.write(row, col, '', total_format)
        col += 1
        worksheet.write(row, col, 'Total', total_format)
        col += 1
        worksheet.write(row, col, round(total_opening, 2), total_format)
        col += 1
        worksheet.write(row, col, round(total_receivable, 2), total_format)
        col += 1
        worksheet.write(row, col, round(total_sales, 2), total_format)
        col += 1
        worksheet.write(row, col, round(total_recovery, 2), total_format)
        col += 1

        if wizard.tax_filter == 'with_tax':
            worksheet.write(row, col, round(total_sale_tax_wh, 2), total_format)
            col += 1
            worksheet.write(row, col, round(total_income_tax_wh, 2), total_format)
            col += 1

        worksheet.write(row, col, round(total_closing, 2), total_format)

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())
        filename = f"Party_Receivable_{wizard.date_from}_{wizard.date_to}.xlsx"

        attachment = wizard.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'res_model': 'tti.report.wizard',
            'res_id': wizard.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        download_url = f'/web/content/{attachment.id}?download=true'
        return {
            "type": "ir.actions.act_url",
            "url": download_url,
            "target": "self",
        }