from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class CRMTeam(models.Model):
    _inherit = 'crm.team'

    client_type = fields.Selection(
        [('contractor', 'Contractor'), ('consultant', 'Consultant'),
         ('normal', 'Normal')],
        string="Client Type", required=True, default='normal')


