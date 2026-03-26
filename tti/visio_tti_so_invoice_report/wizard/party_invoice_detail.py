from odoo import models, fields , api
from odoo.exceptions import ValidationError

class PartyInvoiceDetailWizard(models.TransientModel):
    _name = 'party.invoice.detail.wizard'
    _description = 'Party Invoice Detail Wizard'

    date_from = fields.Date(string='Date From' , required=True)
    date_to = fields.Date(string='Date To' , required=True)
    # manufacturer_id = fields.Many2one('res.partner', string='Manufacturer' , required=True)
    partner_id = fields.Many2one('res.partner', string='Manufacturer' , required=True)
    buyer_id = fields.Many2one('res.partner', string='Buyer')

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError("Date From cannot be greater than Date To.")

    def action_generate_report(self):
        data = {
            'date_from': self.date_from.strftime('%Y-%m-%d') if self.date_from else False,
            'date_to': self.date_to.strftime('%Y-%m-%d') if self.date_to else False,
            'manufacturer_id': self.partner_id.id,
            'buyer_id': self.buyer_id.id,
        }
        return self.env.ref('visio_tti_so_invoice_report.report_party_invoice_detail_pdf').report_action(self, data=data)

