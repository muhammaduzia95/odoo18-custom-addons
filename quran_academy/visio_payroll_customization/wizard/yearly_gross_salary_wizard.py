from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import calendar
from datetime import date


class YearlyGrossSalaryWizard(models.TransientModel):
    _name = "yearly.gross.salary.wizard"
    _description = "Yearly Gross Salary Wizard"

    month_from = fields.Selection(
        [(str(i), calendar.month_name[i]) for i in range(1, 13)],
        string="Month From",
        required=True
    )
    month_to = fields.Selection(
        [(str(i), calendar.month_name[i]) for i in range(1, 13)],
        string="Month To",
        required=True
    )
    year = fields.Integer(
        string="Year",
        required=True,
        default=lambda self: date.today().year
    )

    @api.constrains('month_from', 'month_to')
    def _check_month_range(self):
        for rec in self:
            if rec.month_from and rec.month_to and int(rec.month_from) > int(rec.month_to):
                raise ValidationError(_("Month From cannot be greater than Month To."))

    def action_print_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f"/yearly_gross_salary_statement_worker/export?month_from={self.month_from}&month_to={self.month_to}&year={self.year}",
            'target': 'new',
        }
