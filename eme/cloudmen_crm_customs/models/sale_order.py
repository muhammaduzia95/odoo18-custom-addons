from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        record = super(SaleOrder, self).create(vals)

        # Check if there's an opportunity associated
        if record.opportunity_id and record.opportunity_id.lead_customer_ids:
            # Check if partner already exists in lead_customer_ids
            existing_partner = record.opportunity_id.lead_customer_ids.filtered(
                lambda x: x.partner_id.id == record.partner_id.id
            )

            # If partner doesn't exist, create a new line
            if not existing_partner:
                self.env['crm.lead.customer.line'].create({
                    'partner_id': record.partner_id.id,
                    'lead_id': record.opportunity_id.id,
                    'scope_of_work': record.opportunity_id.name or '',
                    'expected_closing_date': record.opportunity_id.date_deadline,
                })

        return record

    def write(self, vals):
        ret = super(SaleOrder, self).write(vals)

        # If partner_id is being updated
        if 'partner_id' in vals:
            for record in self:
                if record.opportunity_id and record.opportunity_id.lead_customer_ids:
                    # Check if new partner already exists in lead_customer_ids
                    existing_partner = record.opportunity_id.lead_customer_ids.filtered(
                        lambda x: x.partner_id.id == vals['partner_id']
                    )

                    # If partner doesn't exist, create a new line
                    if not existing_partner:
                        self.env['crm.lead.customer.line'].create({
                            'partner_id': vals['partner_id'],
                            'lead_id': record.opportunity_id.id,
                            'scope_of_work': record.opportunity_id.name or '',
                            'expected_closing_date': record.opportunity_id.date_deadline,
                        })

        return ret

    def action_confirm(self):
        ret = super(SaleOrder, self).action_confirm()
        for record in self:
            record.opportunity_id.partner_id = record.partner_id.id

        return ret