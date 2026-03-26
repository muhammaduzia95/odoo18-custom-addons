# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_attendance_portal\controllers\portal_controller_manager_approval.py
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PortalManagerApproval(http.Controller):

    def _is_admin(self):
        return request.env.user.has_group("base.group_system")

    def _get_employee(self):
        return request.env.user.employee_id

    def _domain_for_user(self, employee):
        # Admin: all records
        if self._is_admin():
            return [(1, "=", 1)]
        # Normal manager: only team requests (where subordinate's parent = me)
        if employee:
            return [("employee_id.parent_id", "=", employee.id)]
        # no employee linked -> see nothing
        return [("id", "=", 0)]

    @http.route(["/my/manager-approval"], type="http", auth="user", website=True)
    def portal_manager_approval_list(self, **kw):

        if not self._is_admin() and not request.env.user.has_group(
                "visio_tti_attendance_portal.group_manager_approval_portal"):
            return request.redirect("/my")

        employee = self._get_employee()

        Requests = request.env["tti.attendance.portal.request"].sudo()

        domain = self._domain_for_user(employee)
        # only pending manager verify
        domain += [("state", "=", "draft"), ("employee_id.parent_id", "!=", False)]

        records = Requests.search(domain, order="date desc, id desc")

        values = {
            "employee": employee,
            "requests": records,
            "is_admin": self._is_admin(),
        }
        return request.render("visio_tti_attendance_portal.portal_manager_approval_list", values)

    @http.route(
        ["/my/manager-approval/verify/<int:request_id>"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_manager_approval_verify(self, request_id, **post):

        if not self._is_admin() and not request.env.user.has_group(
                "visio_tti_attendance_portal.group_manager_approval_portal"):
            return request.redirect("/my")

        employee = self._get_employee()

        rec = request.env["tti.attendance.portal.request"].sudo().browse(request_id)

        if not rec.exists():
            return request.redirect("/my/manager-approval")

        # Security check: admin OR manager of that employee
        if not self._is_admin():
            if not employee or rec.employee_id.parent_id.id != employee.id:
                _logger.warning(
                    "[portal_manager_approval_verify] Unauthorized verify attempt. user=%s rec=%s",
                    request.env.user.id, rec.id
                )
                return request.redirect("/my/manager-approval")

        # verify (push to HR approval model)
        rec.sudo().action_verify()
        return request.redirect("/my/manager-approval")
