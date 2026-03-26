from odoo import models, fields, api


class PartyReceivableReportPDF(models.AbstractModel):
    _name = 'report.visio_tti_exel_reports.party_receivable_report_pdf'
    _description = 'Party Receivable PDF Generator'
    _inherit = 'report.report_xlsx.abstract'

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
            opening_domain += [('move_id.tti_si_category_ids', 'in', wizard.category_ids.ids)]

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

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['tti.report.wizard'].browse(docids)

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

        # Calculate closing balances and categories
        for partner_id, data in partner_data_map.items():
            if wizard.tax_filter == 'with_tax':
                data['closing'] = data['opening'] + data['sales'] - data['recovery'] - data['sale_tax_wh'] - data[
                    'income_tax_wh']
            else:
                data['closing'] = data['opening'] + data['sales'] - data['recovery']

            # Get categories from invoices for this partner
            partner_invoices = invoices.filtered(lambda inv: inv.partner_id.id == partner_id)
            categories = ', '.join(
                set(cat.name for inv in partner_invoices for cat in inv.move_id.tti_si_category_ids)) or ''
            data['categories'] = categories

        return {
            'docs': docids,
            'doc_model': 'tti.report.wizard',
            'wizard': wizard,
            'data_map': partner_data_map,
        }