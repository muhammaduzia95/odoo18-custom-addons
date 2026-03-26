from odoo import models, fields

class PartyInvoiceDetailWizard(models.TransientModel):
    _name = 'party.invoice.detail.wizard'
    _description = 'Party Invoice Detail Wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer' , required=True)
    buyer_id = fields.Many2one('res.partner', string='Buyer')

    def action_generate_report(self):
        data = {
            'date_from': self.date_from.strftime('%Y-%m-%d') if self.date_from else False,
            'date_to': self.date_to.strftime('%Y-%m-%d') if self.date_to else False,
            'manufacturer_id': self.manufacturer_id.id,
            'buyer_id': self.buyer_id.id,
        }
        return self.env.ref('visio_tti_so_customize.report_party_invoice_detail_pdf').report_action(self, data=data)

