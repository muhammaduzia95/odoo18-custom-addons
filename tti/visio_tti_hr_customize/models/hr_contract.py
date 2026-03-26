from odoo import models, fields, api , _
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import UserError
from odoo.addons.analytic.models.analytic_mixin import AnalyticMixin

class HrContract(models.Model,AnalyticMixin):
    _inherit = 'hr.contract'

    analytic_dist = fields.Json(string="Analytic Distribution")
    medical_allowance_tti = fields.Monetary(string="Medical Allowance", currency_field='currency_id')
    gross_salary_tti = fields.Monetary(
        string="Gross Salary",
        currency_field='currency_id',
        compute="_compute_gross_salary_tti",
        store=True
    )
    
    

    @api.depends('wage', 'medical_allowance_tti')
    def _compute_gross_salary_tti(self):
        for contract in self:
            contract.gross_salary_tti = contract.wage + contract.medical_allowance_tti

    mess_deduction = fields.Monetary(string="Mess Deduction", currency_field='currency_id')
    tax_deduction = fields.Monetary(string="Tax Deduction", currency_field='currency_id')

    # analytic_account_id = fields.Many2many(
    #     'account.analytic.account', string='Analytic Account', company_dependent=True)

    probation_checklist = fields.Html(
        string="Probation Checklist",
        help="Custom probation checklist for this contract"
    )

    send_probation_reminder = fields.Boolean(
        string="Send Probation Reminder",
        help="Check this to send probation reminder notification to HR users"
    )

    show_probation_tab = fields.Boolean(
        string="Show Probation Tab",
        compute="_compute_show_probation_tab",
        help="Show probation tab only for probation contracts"
    )

    @api.depends('contract_type_id')
    def _compute_show_probation_tab(self):
        """Show probation tab only for probation contracts"""
        for contract in self:
            is_probation = contract.contract_type_id and 'probation' in contract.contract_type_id.name.lower()
            contract.show_probation_tab = is_probation

    @api.model_create_multi
    def create(self, vals):
        """Set default probation checklist when creating probation contract"""
        contract = super().create(vals)
        if contract.show_probation_tab and not contract.probation_checklist:
            contract.probation_checklist = self._get_default_probation_checklist()
        return contract

    def _get_default_probation_checklist(self):
        """Default probation checklist HTML"""
        return """
          <div class="probation-checklist">
              <h4>Probation Checklist</h4>
              <p>Please ensure the following items are completed:</p>
              <ul>
                  <li>☐ Confirmation letter system based</li>
                  <li>☐ Paid leaves setup</li>
                  <li>☐ Health Insurance enrollment</li>
                  <li>☐ Salary Change processing</li>
                  <li>☐ Probation Extension (if needed)</li>
              </ul>
              <p><strong>Notes:</strong></p>
              <p>Add any additional notes or requirements here...</p>
          </div>
          """

    def action_send_probation_notification(self):
        """Send probation reminder notification to HR users via dedicated channel"""
        print("action_send_probation_notification")
        self.ensure_one()

        if not self._is_probation_notification_due():
            return

        hr_users = self.env['res.users'].search([
            ('groups_id', 'in', [self.env.ref('visio_tti_hr_customize.group_probation_manager').id])
        ])
        if not hr_users:
            return

        self._send_probation_activity_notifications(hr_users)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notification Sent!',
                'message': f'Probation reminder sent to {len(hr_users)} HR user(s) as activities',
                'type': 'success',
                'sticky': False,
            }
        }

    def _send_probation_activity_notifications(self, hr_users):
        """Fallback method to send notifications as activities"""
        print("_send_probation_activity_notifications")

        subject = f"Probation Reminder: {self.employee_id.name}"
        note = f"""
            Probation checklist reminder for employee {self.employee_id.name}
            Contract Type: {self.contract_type_id.name}
            Contract Start Date: {self.date_start}
            Contract End Date: {self.date_end or 'Not Set'}
            Please review the probation checklist and complete pending items.
        """

        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            activity_type = self.env['mail.activity.type'].search([], limit=1)

        for user in hr_users:
            self.env['mail.activity'].create({
                'activity_type_id': activity_type.id,
                'summary': subject,
                'note': note,
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get(self._name).id,
                'user_id': user.id,
            })

    def _is_probation_notification_due(self):
        """Return True if contract is probation and today is in the 3rd month"""
        print("_is_probation_notification_due")
        self.ensure_one()

        if not self.contract_type_id or 'probation' not in self.contract_type_id.name.lower():
            return False
        if not self.date_start:
            return False

        today = fields.Date.today()
        third_month_start = self.date_start + relativedelta(months=2)
        third_month_end = self.date_start + relativedelta(months=3)

        return third_month_start <= today < third_month_end

    @api.model
    def cron_send_probation_notifications(self):
        """Cron job to check all probation contracts and send reminders if due"""
        contracts = self.search([
            ('contract_type_id.name', 'ilike', 'probation'),
            ('date_start', '!=', False),
            ('date_end', '!=', False),
        ])
        print("cron running" , contracts)

        for contract in contracts:
            contract.action_send_probation_notification()


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        # Get the base line values
        vals = super()._prepare_line_values(line, account_id, date, debit, credit)

        # Override analytic_distribution with contract's analytic_dist
        if line.slip_id.contract_id.analytic_dist:
            vals['analytic_distribution'] = line.slip_id.contract_id.analytic_dist

        return vals
