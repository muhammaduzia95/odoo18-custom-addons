# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_missed_attendance\models\missed_attendance_request.py
from odoo import models, fields, api
from datetime import timedelta, datetime, time as dt_time
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MissedAttendanceRequest(models.Model):
    _name = 'missed.attendance.request'
    _description = 'Missed Attendance Request'
    _order = 'date desc'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)

    check_in = fields.Datetime(string="Check In", required=True)
    check_out = fields.Datetime(string="Check Out", required=True)

    # just for ordering / reporting
    date = fields.Date(string="Date", compute="_compute_date", store=True)

    reason = fields.Text(string="Reason",)

    # keep the fields if you ever want them later (not used in views now)
    attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment Name")

    # only 2 states now
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
        ],
        default='draft',
        string="Status",
    )

    @api.depends('check_in')
    def _compute_date(self):
        _logger.info("[_compute_date] Computing date for %s records", len(self))
        for rec in self:
            if rec.check_in:
                computed_date = rec.check_in.date()
                _logger.debug(
                    "[_compute_date] rec.id=%s, employee_id=%s, check_in=%s -> date=%s",
                    rec.id, rec.employee_id.id, rec.check_in, computed_date
                )
                rec.date = computed_date
            else:
                _logger.debug(
                    "[_compute_date] rec.id=%s has no check_in, setting date=False",
                    rec.id
                )
                rec.date = False

    def action_approve(self):
        """HR approves → create or fix hr.attendance for that day."""
        _logger.info("[action_approve] Called for records: %s", self.ids)

        for rec in self:
            _logger.info(
                "[action_approve] Processing rec.id=%s, state=%s, employee_id=%s",
                rec.id, rec.state, rec.employee_id.id
            )

            if rec.state == 'approved':
                _logger.info("[action_approve] rec.id=%s already approved, skipping", rec.id)
                continue

            if not rec.employee_id:
                raise UserError("Employee record is missing for this request.")
            if not rec.check_in or not rec.check_out:
                raise UserError("Check In and Check Out are required.")

            # IMPORTANT for internal users / multi-company:
            # ensure env allowed companies includes employee's company
            emp = self.env['hr.employee'].sudo().browse(rec.employee_id.id)
            cid = emp.company_id.id if emp.company_id else False

            Attendance = self.env['hr.attendance'].sudo().with_context(
                allowed_company_ids=[cid] if cid else self.env.companies.ids,
                force_company=cid or self.env.company.id,
            )

            # Use datetime range (not date) for check_in domain
            day_start_dt = datetime.combine(rec.check_in.date(), dt_time.min)
            day_end_dt = day_start_dt + timedelta(days=1)

            domain = [
                ('employee_id', '=', emp.id),
                ('check_in', '>=', day_start_dt),
                ('check_in', '<', day_end_dt),
            ]
            _logger.info("[action_approve] Searching hr.attendance domain=%s", domain)

            existing = Attendance.search(domain, order='check_in asc')
            _logger.info("[action_approve] Found %s hr.attendance records", len(existing))

            if not existing:
                att = Attendance.create({
                    'employee_id': emp.id,
                    'check_in': rec.check_in,
                    'check_out': rec.check_out,
                })
                _logger.info("[action_approve] Created hr.attendance id=%s for request id=%s", att.id, rec.id)
            else:
                att = existing[0]
                att.write({
                    'check_in': rec.check_in,
                    'check_out': rec.check_out,
                })
                _logger.info("[action_approve] Updated hr.attendance id=%s for request id=%s", att.id, rec.id)

            rec.state = 'approved'
            _logger.info("[action_approve] rec.id=%s state set to approved", rec.id)


