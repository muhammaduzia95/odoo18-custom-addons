from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class CRMStage(models.Model):
    _inherit = 'crm.stage'

    is_tender_stage = fields.Boolean(string = 'Is Tender', default=False)