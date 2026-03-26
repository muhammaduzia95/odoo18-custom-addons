from odoo import models, fields, api
from datetime import date


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    dollar_rate = fields.Float(
        string="Dollar Price",
        digits='Product Price'
    )

    fixed_price = fields.Float(string="Fixed Price", digits='Product Price', compute="_compute_dollar_rate")

    @api.depends('dollar_rate','currency_id', 'pricelist_id', 'pricelist_id.currency_id', 'pricelist_id.currency_id.rate_ids.rate')
    def _compute_dollar_rate(self):
        """When user enters Dollar Price, update Fixed Price in local currency"""
        usd_currency = self.env.ref('base.USD')
        today = date.today()

        for record in self:
            # if record.dollar_rate and record.pricelist_id.currency_id:
            currency = record.pricelist_id.currency_id

            if currency == usd_currency:
                record.fixed_price = record.dollar_rate
            else:
                rate = currency._get_conversion_rate(usd_currency, currency, record.env.company, today)
                record.fixed_price = record.dollar_rate * rate
