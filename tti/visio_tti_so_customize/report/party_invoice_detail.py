from odoo import models

class PartyInvoiceDetailReport(models.AbstractModel):
    _name = 'report.visio_tti_so_customize.party_invoice_template'
    _description = 'Party Invoice Detail Report'

    def _get_report_values(self, docids, data=None):
        docids = docids or self.env.context.get('active_ids', [])
        doc = self.env['party.invoice.detail.wizard'].browse(docids)
        manufacturer = self.env['res.partner'].browse(data.get('manufacturer_id'))
        buyer = self.env['res.partner'].browse(data.get('buyer_id')) if data.get('buyer_id') else False

        domain = [('partner_id', '=', manufacturer.id)]
        if buyer:
            domain.append(('tti_pi_buyer', '=', buyer.id))

        sale_orders = self.env['sale.order'].search(domain)
        print("sale orders" , len(sale_orders))
        invoices = sale_orders.mapped('invoice_ids').filtered(lambda inv: inv.move_type == 'out_invoice')
        print("sale invoicea", len(invoices))

        return {
            'doc_ids': docids,
            'doc_model': 'party.invoice.detail.wizard',
            'docs': doc,
            'data': data,
            'manufacturer': manufacturer,
            'buyer': buyer,
            'invoices': invoices,
            'sale_orders': sale_orders,
        }
