# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_attendance_portal\controllers\portal_controller_marketing_att.py
from odoo import http, fields
from odoo.http import request
from datetime import datetime, date, timedelta
import pytz
import logging
import re
from calendar import monthrange


_logger = logging.getLogger(__name__)


class PortalMarketingAttendance(http.Controller):

    def _local_to_utc(self, date_str, time_str):
        """
        Accepts:
          - 24h: '19:30' or '19:30:00'
          - 12h: '7:30 PM' or '07:30 pm'
        Returns: UTC naive datetime (Odoo standard storage)
        """
        if not date_str or not time_str:
            raise ValueError("Missing date/time")

        date_str = (date_str or "").strip()
        time_str = (time_str or "").strip()

        # Parse date
        d = date.fromisoformat(date_str)

        # Parse time (24h OR 12h with AM/PM)
        m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp][Mm])?$", time_str)
        if not m:
            raise ValueError(f"Unsupported time format: {time_str}")

        hour = int(m.group(1))
        minute = int(m.group(2))
        second = int(m.group(3) or 0)
        ampm = m.group(4)

        if ampm:
            ampm = ampm.lower()
            if hour == 12:
                hour = 0
            if ampm == "pm":
                hour += 12

        if hour > 23 or minute > 59 or second > 59:
            raise ValueError(f"Invalid time values: {time_str}")

        local_naive = datetime(d.year, d.month, d.day, hour, minute, second)

        user_tz = request.env.user.tz or "Asia/Karachi"
        tz = pytz.timezone(user_tz)

        local_aware = tz.localize(local_naive, is_dst=None)
        utc_aware = local_aware.astimezone(pytz.UTC)
        return utc_aware.replace(tzinfo=None)

    def _utc_to_local(self, dt):
        """Convert Odoo stored UTC naive datetime -> user's local naive datetime (for portal display only)."""
        if not dt:
            return False
        user_tz = request.env.user.tz or "Asia/Karachi"
        tz = pytz.timezone(user_tz)
        utc_aware = pytz.UTC.localize(dt)  # dt is UTC naive in Odoo
        return utc_aware.astimezone(tz).replace(tzinfo=None)

    # Helpers
    def _get_employee(self):
        employee = request.env.user.employee_id
        user = request.env.user
        _logger.info("[_get_employee] Using request.env.user.employee_id -> %s", employee)
        if employee:
            return employee
        else:
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            _logger.info("[employee orm ] user=%s", employee and employee.id)

            return employee

    def _get_month_data(self, employee):
        _logger.info("[_get_month_data] Start, employee=%s", employee and f"{employee.id} - {employee.name}")
        month_lines = []
        missing_days = []

        if not employee:
            _logger.warning("[_get_month_data] No employee provided, returning empty lists")
            return month_lines, missing_days

        today = fields.Date.context_today(request.env.user)
        first_day = today.replace(day=1)
        _logger.info("[_get_month_data] today=%s, first_day_of_month=%s", today, first_day)
        last_day = date(today.year, today.month, monthrange(today.year, today.month)[1])

        Attendance = request.env["hr.attendance"].sudo()
        Leave = request.env["hr.leave"].sudo()

        from datetime import time as dt_time

        start_dt = datetime.combine(first_day, dt_time.min)
        end_dt = datetime.combine(today + timedelta(days=1), dt_time.min)

        attendance_domain = [
            ("employee_id", "=", employee.id),
            ("check_in", ">=", start_dt),
            ("check_in", "<", end_dt),
        ]

        _logger.debug("[_get_month_data] Attendance search domain=%s", attendance_domain)
        attendances = Attendance.search(attendance_domain)
        _logger.info("[_get_month_data] Found %s attendance records", len(attendances))

        # Map date -> {check_in, check_out}
        attendance_by_date = {}
        for att in attendances:
            if not att.check_in:
                _logger.debug("[_get_month_data] Skipping attendance id=%s with no check_in", att.id)
                continue
            d = att.check_in.date()
            data = attendance_by_date.setdefault(d, {"check_in": False, "check_out": False})
            # earliest check_in
            if not data["check_in"] or att.check_in < data["check_in"]:
                data["check_in"] = att.check_in
            # latest check_out
            if att.check_out:
                if not data["check_out"] or att.check_out > data["check_out"]:
                    data["check_out"] = att.check_out

        # Approved leaves (validated)
        leave_domain = [
            ("employee_id", "=", employee.id),
            ("state", "=", "validate"),
            ("request_date_from", "<=", last_day),
            ("request_date_to", ">=", first_day),
        ]
        _logger.debug("[_get_month_data] Leave search domain=%s", leave_domain)
        leaves = Leave.search(leave_domain)

        # Map date -> list of leaves
        leave_by_date = {}
        for lv in leaves:
            d = lv.request_date_from
            while d <= lv.request_date_to:
                if first_day <= d <= today:
                    leave_by_date.setdefault(d, []).append(lv)
                d += timedelta(days=1)

        # ---- Public Holidays ----
        CalLeave = request.env["resource.calendar.leaves"].sudo()
        public_by_date = {}

        public_leaves = CalLeave.search([
            ("resource_id", "=", False),
            ("company_id", "in", [False, employee.company_id.id]),
            ("date_from", "<", end_dt),
            ("date_to", ">=", start_dt),
        ])

        for ph in public_leaves:
            start_local = self._utc_to_local(ph.date_from)
            end_local = self._utc_to_local(ph.date_to)
            if not start_local or not end_local:
                continue

            d = start_local.date()
            end_d = end_local.date()
            while d <= end_d:
                if first_day <= d <= today:
                    public_by_date.setdefault(d, []).append(ph.name or "Public Holiday")
                d += timedelta(days=1)

        current = first_day
        while current <= last_day:
            att_data = attendance_by_date.get(current)
            leave_list = leave_by_date.get(current, [])
            public_list = public_by_date.get(current, [])

            # Build leave text
            leave_texts = []
            for l in leave_list:
                leave_type = l.holiday_status_id.name or "Leave"
                leave_name = (l.name or "").strip()
                leave_texts.append(f"{leave_type} - {leave_name}" if leave_name else leave_type)
            for ph_name in public_list:
                leave_texts.append(ph_name)
            leave_text = ", ".join(leave_texts)

            # For Sundays with no leave, show "Sunday" in leave column
            leave_text_for_line = leave_text
            if not leave_text_for_line and current.weekday() == 6:
                leave_text_for_line = "Sunday"

            has_full_attendance = bool(att_data and att_data.get("check_in") and att_data.get("check_out"))

            # TABLE 2
            if has_full_attendance or leave_list or public_list or current.weekday() == 6:
                ci = att_data["check_in"] if att_data else False
                co = att_data["check_out"] if att_data else False
                month_lines.append({
                    "date": current,
                    "check_in": ci,
                    "check_out": co,
                    "check_in_display": self._utc_to_local(ci) if ci else False,
                    "check_out_display": self._utc_to_local(co) if co else False,
                    "leave_text": leave_text_for_line,
                })

            # TABLE 3 (excluding Sundays)
            missing_condition = False
            if current.weekday() != 6 and not public_list:
                if not att_data and not leave_list:
                    missing_condition = True
                elif att_data and not leave_list and (not att_data.get("check_in") or not att_data.get("check_out")):
                    missing_condition = True

            if missing_condition:
                ci = att_data.get("check_in") if att_data else False
                co = att_data.get("check_out") if att_data else False
                missing_days.append({
                    "date": current,
                    "check_in": ci,
                    "check_out": co,
                    "check_in_display": self._utc_to_local(ci) if ci else False,
                    "check_out_display": self._utc_to_local(co) if co else False,
                })

            current += timedelta(days=1)

        return month_lines, missing_days

    # LIST PAGE
    @http.route(["/my/marketing-attendance"], type="http", auth="user", website=True)
    def portal_marketing_attendance_list(self, **kw):
        _logger.info("[portal_marketing_attendance_list] Called with kw=%s", kw)
        employee = self._get_employee()
        month_lines, missing_days = self._get_month_data(employee) if employee else ([], [])

        Requests = request.env["tti.attendance.portal.request"].sudo()
        req_domain = [("employee_id", "=", employee.id)] if employee else [("id", "=", 0)]

        # optional but recommended so marketing page doesn't show missed-attendance requests:
        req_domain += [("reason", "=ilike", "Official Visit%")]

        marketing_requests = Requests.search(req_domain, order="date desc, id desc")

        values = {
            "employee": employee,
            "missed_list": marketing_requests,  # keep key same to avoid template changes
            "month_lines": month_lines,
            "missing_days": missing_days,
        }
        return request.render("visio_tti_attendance_portal.marketing_attendance_list", values)

    # CREATE FORM PAGE
    @http.route("/my/marketing-attendance/new", type="http", auth="user", website=True)
    def portal_marketing_attendance_create(self, **kw):
        _logger.info("[portal_marketing_attendance_create] Called with kw=%s", kw)
        employee = self._get_employee()
        _, missing_days = self._get_month_data(employee) if employee else ([], [])

        values = {
            "employee": employee,
            "missing_days": missing_days,
        }
        return request.render("visio_tti_attendance_portal.marketing_attendance_create", values)

    # SUBMIT FORM
    @http.route("/my/marketing-attendance/submit", type="http", auth="user",
                methods=["POST"], website=True, csrf=False)
    def portal_marketing_attendance_submit(self, **post):
        _logger.info("[portal_marketing_attendance_submit] Called with post=%s", post)
        employee = self._get_employee()
        if not employee:
            return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                "error_message": "No employee is linked to your portal user."
            })

        selected_date_str = (post.get("date") or "").strip()
        if not selected_date_str:
            return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                "error_message": "Please select a date."
            })

        try:
            selected_date = date.fromisoformat(selected_date_str)
        except ValueError:
            return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                "error_message": "Invalid date format."
            })

        # Ensure selected date is allowed (missing/partial + no leave)
        _, missing_days = self._get_month_data(employee)
        missing_map = {line["date"]: line for line in missing_days}
        day_info = missing_map.get(selected_date)

        if not day_info:
            return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                "error_message": "You can only request for days with missing/partial attendance and no leave."
            })

        existing_ci = day_info.get("check_in")
        existing_co = day_info.get("check_out")

        ci_time_str = (post.get("check_in_time") or "").strip()
        co_time_str = (post.get("check_out_time") or "").strip()

        check_in_dt = existing_ci
        check_out_dt = existing_co

        # Case 1: has CI, missing CO
        if existing_ci and not existing_co:
            if not co_time_str:
                return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                    "error_message": "Please enter Check Out time for this day."
                })
            try:
                check_out_dt = self._local_to_utc(selected_date_str, co_time_str)
            except Exception:
                return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                    "error_message": "Invalid Check Out time format."
                })

        # Case 2: has CO, missing CI
        elif existing_co and not existing_ci:
            if not ci_time_str:
                return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                    "error_message": "Please enter Check In time for this day."
                })
            try:
                check_in_dt = self._local_to_utc(selected_date_str, ci_time_str)
            except Exception:
                return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                    "error_message": "Invalid Check In time format."
                })

        # Case 3: no attendance at all
        elif not existing_ci and not existing_co:
            if not ci_time_str or not co_time_str:
                return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                    "error_message": "Check In and Check Out time are required for this day."
                })
            try:
                check_in_dt = self._local_to_utc(selected_date_str, ci_time_str)
                check_out_dt = self._local_to_utc(selected_date_str, co_time_str)
            except Exception:
                return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                    "error_message": "Invalid time format."
                })
        else:
            return request.render("visio_tti_attendance_portal.marketing_portal_error", {
                "error_message": "Attendance for this day is already complete."
            })

        reason = (post.get("reason") or "").strip() or "Official Visit."
        # optional but recommended so the list filter always works even if user edits reason:
        if not reason.lower().startswith("official visit"):
            reason = f"Official Visit. {reason}"

        portal_req = request.env["tti.attendance.portal.request"].sudo().create({
            "employee_id": employee.id,
            "check_in": check_in_dt,
            "check_out": check_out_dt,
            "reason": reason,
            "state": "draft",
        })

        # If employee has NO manager, push directly to HR approval
        if not employee.parent_id:
            portal_req.sudo().action_verify()

        return request.redirect("/my/marketing-attendance")
