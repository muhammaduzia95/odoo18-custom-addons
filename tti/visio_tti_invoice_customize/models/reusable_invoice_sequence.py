from odoo import models, fields, api
from odoo.exceptions import ValidationError
from contextlib import contextmanager
from datetime import datetime


class ReusableInvoiceSequence(models.Model):
    _name = 'reusable.invoice.sequence'
    _description = 'Reusable Invoice Sequences'

    state_code = fields.Char(required=True)  # 'PB', 'SD', etc.
    sequence_value = fields.Char(required=True)  # e.g., 'P-00015'
    month_year = fields.Char(
        string='Month Year',
        default=lambda self: fields.Date.context_today(self).strftime('%m%y'),
        required=True
    )
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

