# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_attendance_portal\models\tti_attendance_portal.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class TtiAttendancePortalRequest(models.Model):
    _name = "tti.attendance.portal.request"
    _description = "TTI Attendance Portal Request"
    _order = "date desc, id desc"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    check_in = fields.Datetime(string="Check In", required=True)
    check_out = fields.Datetime(string="Check Out", required=True)
    date = fields.Date(string="Date", compute="_compute_date", store=True)
    reason = fields.Text(string="Reason")
    attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment Name")

    hr_approval_id = fields.Many2one(
        "tti.hr.attendance.approval",
        string="HR Approval",
        readonly=True,
        copy=False,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("verified", "Verified"),
        ],
        default="draft",
        string="Status",
        tracking=True,
    )

    @api.depends("check_in")
    def _compute_date(self):
        for rec in self:
            rec.date = rec.check_in.date() if rec.check_in else False

    def action_verify(self):
        """Manager verifies -> push to HR approval model."""
        for rec in self:
            if rec.state != "draft":
                continue

            if not rec.employee_id or not rec.check_in or not rec.check_out:
                raise UserError(_("Employee, Check In and Check Out are required."))

            if rec.hr_approval_id:
                # already pushed
                rec.state = "verified"
                continue

            approval = self.env["tti.hr.attendance.approval"].sudo().create({
                "employee_id": rec.employee_id.id,
                "check_in": rec.check_in,
                "check_out": rec.check_out,
                "reason": rec.reason,
                "portal_request_id": rec.id,
                "state": "verified",
            })

            rec.hr_approval_id = approval.id
            rec.state = "verified"

