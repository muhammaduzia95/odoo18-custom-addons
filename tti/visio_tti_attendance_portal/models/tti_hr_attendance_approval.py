# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_attendance_portal\models\tti_hr_attendance_approval.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta, time as dt_time
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class TtiHrAttendanceApproval(models.Model):
    _name = "tti.hr.attendance.approval"
    _description = "TTI HR Attendance Approval"
    _order = "date desc, id desc"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    check_in = fields.Datetime(string="Check In", required=True)
    check_out = fields.Datetime(string="Check Out", required=True)
    date = fields.Date(string="Date", compute="_compute_date", store=True)
    reason = fields.Text(string="Reason")

    portal_request_id = fields.Many2one(
        "tti.attendance.portal.request",
        string="Portal Request",
        readonly=True,
        ondelete="set null",
    )

    state = fields.Selection(
        [
            ("verified", "Verified"),
            ("approved", "Approved"),
        ],
        default="verified",
        string="Status",
        tracking=True,
    )

    @api.depends("check_in")
    def _compute_date(self):
        for rec in self:
            rec.date = rec.check_in.date() if rec.check_in else False

    def action_approve(self):
        """HR approves -> create/update hr.attendance for that day."""
        for rec in self:
            if rec.state == "approved":
                continue

            if not rec.employee_id or not rec.check_in or not rec.check_out:
                raise UserError(_("Employee, Check In and Check Out are required."))

            if rec.check_in >= rec.check_out:
                raise UserError(_("Check In must be earlier than Check Out."))

            emp = self.env["hr.employee"].sudo().browse(rec.employee_id.id)
            cid = emp.company_id.id if emp.company_id else False

            Attendance = self.env["hr.attendance"].sudo().with_context(
                allowed_company_ids=[cid] if cid else self.env.companies.ids,
                force_company=cid or self.env.company.id,
            )

            day_start_dt = datetime.combine(rec.check_in.date(), dt_time.min)
            day_end_dt = day_start_dt + timedelta(days=1)

            domain = [
                ("employee_id", "=", emp.id),
                ("check_in", ">=", day_start_dt),
                ("check_in", "<", day_end_dt),
            ]

            existing = Attendance.search(domain, order="check_in asc")
            if not existing:
                Attendance.create({
                    "employee_id": emp.id,
                    "check_in": rec.check_in,
                    "check_out": rec.check_out,
                })
            else:
                existing[0].write({
                    "check_in": rec.check_in,
                    "check_out": rec.check_out,
                })

            rec.state = "approved"

