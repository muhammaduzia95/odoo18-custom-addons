from odoo import models, fields, api
from collections import defaultdict

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    leave_summary = fields.Json(string="Leave Summary", compute="_compute_leave_summary", store=False)

    hr = fields.Many2one('hr.employee' , string="HR")

    def _compute_leave_summary(self):
        for employee in self:
            summary = defaultdict(lambda: {'allocated': 0.0, 'used': 0.0, 'remaining': 0.0})

            # 1. Fetch VALIDATED allocations
            allocations = self.env['hr.leave.allocation'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate')
            ])
            for alloc in allocations:
                leave_type = alloc.holiday_status_id.name
                summary[leave_type]['allocated'] += alloc.number_of_days or 0.0

            # 2. Fetch VALIDATED leaves
            approved_leaves = self.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                # ('state', '=', 'validate')
            ])
            for leave in approved_leaves:
                leave_type = leave.holiday_status_id.name
                summary[leave_type]['used'] += leave.number_of_days or 0.0

            # 3. Compute remaining
            for leave_type, values in summary.items():
                values['remaining'] = values['allocated'] - values['used']
                if values['remaining'] < 0:
                    values['remaining'] = 0.0  # prevent negative

            employee.leave_summary = summary

class ResUsers(models.Model):
    _inherit = 'res.users'

    has_timeoff_group = fields.Boolean(compute='_compute_has_timeoff_group', store=False)

    def _compute_has_timeoff_group(self):
        custom_group = self.env['res.groups'].search([('name', '=', 'Employee Portal Users_2')], limit=1)
        for user in self:
            user.has_timeoff_group = custom_group in user.groups_id if custom_group else False