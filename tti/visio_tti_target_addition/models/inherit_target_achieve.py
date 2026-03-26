from odoo import models, fields, api
from calendar import monthrange
from datetime import date


class TargetAchieve(models.Model):
    _inherit = "target.achieve"

    v_date_from = fields.Date(string="Valid From")
    v_date_to = fields.Date(string="Valid To")

    @api.onchange('v_date_from')
    def _onchange_v_date_from(self):
        """
        Convert any selected date -> 1st day of that month
        """
        if self.v_date_from:
            year = self.v_date_from.year
            month = self.v_date_from.month
            self.v_date_from = date(year, month, 1)

    @api.onchange('v_date_to')
    def _onchange_v_date_to(self):
        """
        Convert any selected date -> LAST day of that month
        """
        if self.v_date_to:
            year = self.v_date_to.year
            month = self.v_date_to.month
            last_day = monthrange(year, month)[1]
            self.v_date_to = date(year, month, last_day)
