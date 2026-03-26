from collections import defaultdict
from odoo import models


class PartyInvoiceDetailReport(models.AbstractModel):
    _name = 'report.visio_tti_so_invoice_report.party_invoice_template'
    _description = 'Party Invoice Detail Report'

    def _get_report_values(self, docids, data=None):
        docids = docids or self.env.context.get('active_ids', [])
        wizard = self.env['party.invoice.detail.wizard'].browse(docids)
        manufacturer = self.env['res.partner'].browse(data.get('manufacturer_id'))
        selected_buyer = self.env['res.partner'].browse(data.get('buyer_id')) if data.get('buyer_id') else False
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        credit = manufacturer.credit

        # Step 1: Fetch relevant invoices
        invoice_domain = [
            ('partner_id', '=', manufacturer.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]
        invoices = self.env['account.move'].search(invoice_domain)

        # Step 2: Fetch related sale orders from those invoices
        related_sale_orders = invoices.mapped('sale_order_ids')

        # Step 3: Apply buyer filter if given
        if selected_buyer:
            related_sale_orders = related_sale_orders.filtered(lambda so: so.tti_pi_buyer.id == selected_buyer.id)

        # Step 4: Group sale orders & invoices by buyer
        buyer_groups = []
        groups = defaultdict(lambda: {
            'sale_orders': self.env['sale.order'],
            'invoices': self.env['account.move']
        })

        for so in related_sale_orders:
            buyer = so.tti_pi_buyer
            groups[buyer]['sale_orders'] |= so
            groups[buyer]['invoices'] |= so.invoice_ids.filtered(lambda inv: inv in invoices)

        for buyer, data_group in groups.items():
            buyer_groups.append({
                'buyer': buyer,
                'sale_orders': data_group['sale_orders'],
                'invoices': data_group['invoices'],
            })

        # Step 5: Handle no matching data
        if not buyer_groups:
            buyer_groups.append({
                'buyer': selected_buyer or self.env['res.partner'],
                'sale_orders': self.env['sale.order'],
                'invoices': self.env['account.move'],
            })

        return {
            'doc_ids': docids,
            'doc_model': 'party.invoice.detail.wizard',
            'docs': wizard,
            'data': data,
            'manufacturer': manufacturer,
            'buyer_groups': buyer_groups,
            'selected_buyer': selected_buyer,
            'credit': credit,
        }
