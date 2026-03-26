# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_marketing_attendance_portal\models\marketing_attendance_request.py
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MarketingAttendanceRequest(models.Model):
    _name = 'marketing.attendance.request'
    _description = 'Marketing Attendance Request'
    _order = 'date desc'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    check_in = fields.Datetime(string="Check In", required=True)
    check_out = fields.Datetime(string="Check Out", required=True)

    # ordering/reporting
    date = fields.Date(string="Date", compute="_compute_date", store=True)

    reason = fields.Text(string="Reason")

    attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment Name")

    missed_request_id = fields.Many2one(
        'missed.attendance.request',
        string="Missed Attendance Request",
        readonly=True,
        copy=False, )

    state = fields.Selection([('draft', 'Draft'), ('verify', 'Verify'), ],
                             default='draft', string="Status", )

    @api.depends('check_in')
    def _compute_date(self):
        _logger.info("[_compute_date] Computing date for %s records", len(self))
        for rec in self:
            rec.date = rec.check_in.date() if rec.check_in else False

    def action_verify(self):
        """
        Verify marketing request:
        - create a record in missed.attendance.request
        - mark this marketing request as verified
        (HR will approve missed.attendance.request to create hr.attendance)
        """
        _logger.info("[action_verify] Called for marketing requests: %s", self.ids)

        Missed = self.env['missed.attendance.request'].sudo()

        for rec in self:
            _logger.info(
                "[action_verify] Processing id=%s state=%s employee=%s",
                rec.id, rec.state, rec.employee_id.id if rec.employee_id else None
            )

            if rec.state == 'verify':
                _logger.info("[action_verify] id=%s already verified, skipping", rec.id)
                continue

            if not rec.employee_id:
                raise UserError("Employee record is missing for this request.")
            if not rec.check_in or not rec.check_out:
                raise UserError("Check In and Check Out are required.")
            if rec.check_in > rec.check_out:
                raise UserError("Check In cannot be after Check Out.")

            # prevent duplicate creation
            if rec.missed_request_id:
                _logger.warning(
                    "[action_verify] id=%s already has missed_request_id=%s. Just setting verify state.",
                    rec.id, rec.missed_request_id.id
                )
                rec.state = 'verify'
                continue

            missed_vals = {
                "employee_id": rec.employee_id.id,
                "check_in": rec.check_in,
                "check_out": rec.check_out,
                "reason": rec.reason or "Marketing Attendance (Verified)",
                # attachment fields exist on missed model too in your code
                "attachment": rec.attachment,
                "attachment_name": rec.attachment_name,
            }

            missed_rec = Missed.create(missed_vals)
            _logger.info(
                "[action_verify] Created missed.attendance.request id=%s from marketing id=%s",
                missed_rec.id, rec.id
            )

            rec.missed_request_id = missed_rec.id
            rec.state = 'verify'

        return {'type': 'ir.actions.client', 'tag': 'reload'}
