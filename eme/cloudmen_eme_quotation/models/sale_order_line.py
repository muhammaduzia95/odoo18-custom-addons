from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    default_code = fields.Char(related="product_template_id.default_code")
    # brand = fields.Char(related="product_template_id.brand") #zia comment

    line_section_amount = fields.Float(string='Section Amount', compute="_compute_line_section_amount")
