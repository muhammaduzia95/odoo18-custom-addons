# D:\Visiomate\Odoo\odoo18\custom_addons\tti\hr_zk_attendance\models\biometric_device_details.py
import datetime
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import requests
from datetime import timedelta

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connect the biometric device with odoo"""
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'

    name = fields.Char(string='Name', required=True, help='Record Name')
    device_ip = fields.Char(string='Device IP', help='The IP address of the Device')
    disable_device_during_sync = fields.Boolean(string='Disable Device During Sync', default=False,
                                                help='The IP address of the Device')
    port_number = fields.Integer(string='Port Number', help="The Port Number of the Device")
    address_id = fields.Many2one('res.partner', string='Working Address', help='Working address of the partner')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id,
                                 help='Current Company')

    # ---- WDMS/BioTime integration fields ----
    protocol = fields.Selection(
        [("device", "ZK Device (port 4370)"), ("wdms", "WDMS/BioTime Server (HTTP)")],
        default="device", required=True,
        help="Choose WDMS for servers like http://223.123.42.94:8080"
    )
    wdms_base_url = fields.Char(string="WDMS Base URL", help="e.g., http://223.123.42.94:8080")
    wdms_username = fields.Char(string="WDMS Username")
    wdms_password = fields.Char(string="WDMS Password")
    wdms_static_token = fields.Char(string="WDMS Static Token",
                                    help="(Optional) Paste JWT token from portal Network tab")
    wdms_token = fields.Char(string="WDMS Cached Token", readonly=True)
    wdms_last_sync = fields.Datetime(string="WDMS Last Sync", readonly=True)

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    # def action_test_connection(self):
    #     """Checking the connection status"""
    #     zk = ZK(self.device_ip, port=self.port_number, timeout=35, password=False, ommit_ping=True)
    #     try:
    #         if zk.connect():
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'message': 'Successfully Connected',
    #                     'type': 'success',
    #                     'sticky': False
    #                 }
    #             }
    #     except Exception as error:
    #         raise ValidationError(f'{error}')

    def action_test_connection(self):
        """Checking the connection status for DEVICE or WDMS."""
        self.ensure_one()
        if self.protocol == "wdms":
            # WDMS: call /iclock/api/terminals/ (needs JWT header)
            self._wdms_request("GET", "/iclock/api/terminals/", params={"page_size": 1})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'message': 'WDMS Connected (terminals reachable)', 'type': 'success', 'sticky': False}
            }

        # DEVICE (raw ZK 4370): keep original flow
        zk = ZK(self.device_ip, port=self.port_number, timeout=35, password=False, ommit_ping=True)
        try:
            if zk.connect():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'message': 'Successfully Connected', 'type': 'success', 'sticky': False}
                }
        except Exception as error:
            raise ValidationError(f'{error}')

    def action_set_timezone(self):
        """Function to set user's timezone to device"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=35, password=0, force_udp=False, ommit_ping=True)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'
                user_timezone_time = pytz.utc.localize(fields.Datetime.now())
                user_timezone_time = user_timezone_time.astimezone(pytz.timezone(user_tz))
                conn.set_time(user_timezone_time)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Successfully Set the Time',
                        'type': 'success',
                        'sticky': False
                    }
                }
            else:
                raise UserError(_("Please Check the Connection"))

    def action_clear_attendance(self):
        """Methode to clear record from the zk.machine.attendance model and
        from the device"""
        for info in self:
            try:
                address_id = False
                if info.address_id:
                    address_id = info.address_id.id
                # machine_ip = info.device_ip
                # zk_port = info.port_number
                # try:
                #     # Connecting with the device
                #     zk = ZK(machine_ip, port=zk_port, timeout=30,
                #             password=0, force_udp=False, ommit_ping=True)
                # except NameError:
                #     raise UserError(_(
                #         "Please install it with 'pip3 install pyzk'."))
                # Clearing data from attendance log
                if address_id:
                    self._cr.execute(f"""delete from zk_machine_attendance where address_id = {address_id}""")
                else:
                    self._cr.execute("""delete from zk_machine_attendance""")
                # conn = self.device_connect(zk)
                # if conn:
                #     conn.enable_device()
                #     clear_data = zk.get_attendance()
                #     if clear_data:
                #         # Clearing data in the device
                #         conn.clear_attendance()
                #         # Clearing data from attendance log
                #         self._cr.execute(
                #             """delete from zk_machine_attendance""")
                #         conn.disconnect()
                #     else:
                #         raise UserError(
                #             _('Unable to clear Attendance log.Are you sure '
                #               'attendance log is not empty.'))
                # else:
                #     raise UserError(
                #         _('Unable to connect to Attendance Device. Please use Test Connection button to verify.'))
            except Exception as error:
                raise ValidationError(f'{error}')

    # =================== WDMS HELPERS ===================

    def _wdms_endpoint(self, path):
        self.ensure_one()
        base = (self.wdms_base_url or "").rstrip("/")
        if not base:
            raise UserError(_("Set WDMS Base URL on the device record."))
        return f"{base}{path}"

    def _wdms_headers(self, refresh=False):
        # Use pasted token if present, else fetch with username/password
        token = self.wdms_static_token or self._wdms_get_token(force=refresh)
        return {"Content-Type": "application/json", "Authorization": f"JWT {token}"}

    def _wdms_get_token(self, force=False):
        self.ensure_one()
        if self.wdms_token and not force:
            return self.wdms_token
        if not self.wdms_username or not self.wdms_password:
            raise UserError(_("Set WDMS Username/Password (usually same as portal login)."))
        for ep in ("/jwt-api-token-auth/", "/api-token-auth/"):
            url = self._wdms_endpoint(ep)
            r = requests.post(url, json={"username": self.wdms_username, "password": self.wdms_password}, timeout=30)
            if r.status_code == 200 and isinstance(r.json(), dict) and r.json().get("token"):
                token = r.json()["token"]
                self.sudo().write({"wdms_token": token})
                return token
            _logger.warning("WDMS token attempt %s failed: %s %s", url, r.status_code, r.text[:200])
        raise UserError(_("Unable to obtain WDMS token—check URL/creds and connectivity."))

    def _wdms_request(self, method, path, params=None):
        url = self._wdms_endpoint(path)
        hdr = self._wdms_headers(refresh=False)
        r = requests.request(method, url, headers=hdr, params=params, timeout=60)
        if r.status_code == 401:
            hdr = self._wdms_headers(refresh=True)
            r = requests.request(method, url, headers=hdr, params=params, timeout=60)
        if not (200 <= r.status_code < 300):
            raise UserError(_("WDMS API failed (%s): %s") % (r.status_code, r.text[:400]))
        try:
            return r.json()
        except Exception:
            return r.content

    # @api.model
    # def cron_download(self):
    #     machines = self.env['biometric.device.details'].sudo().search([])
    #     for machine in machines:
    #         machine.action_download_attendance()

    @api.model
    def cron_download(self):
        machines = self.env['biometric.device.details'].sudo().search([])
        for machine in machines:
            if machine.protocol == "wdms":
                machine.action_download_attendance_wdms()
            else:
                machine.action_download_attendance()

    def action_download_attendance(self):
        """Downloads and stores raw attendance logs from the device into zk.machine.attendance only."""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']

        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=35, password=0, force_udp=False, ommit_ping=True)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))

            conn = self.device_connect(zk)
            self.action_set_timezone()

            if conn:
                if info.disable_device_during_sync:
                    conn.disable_device()  # Device Cannot be used during this time.

                user = conn.get_users()
                attendance = conn.get_attendance()
                _logger.info(f"Users len = {len(user)}")
                _logger.info(f"Attendances len = {len(attendance)}")

                if attendance:
                    for each in attendance:
                        atten_time = each.timestamp
                        # local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
                        local_tz = pytz.timezone('Asia/Karachi')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        atten_time = datetime.datetime.strptime(utc_dt.strftime("%Y-%m-%d %H:%M:%S"),
                                                                "%Y-%m-%d %H:%M:%S")
                        atten_time = fields.Datetime.to_string(atten_time)
                        # cutoff_date = datetime.datetime(2025, 10, 1, 0, 0, 0)
                        # if atten_time > fields.Datetime.to_string(cutoff_date):
                        #     continue
                        matched_user = next((u for u in user if u.user_id == each.user_id), None)
                        if not matched_user:
                            continue

                        employee = self.env['hr.employee'].sudo().search([('device_id_num', '=', each.user_id)],
                                                                         limit=1)
                        if not employee:
                            continue
                            # employee = self.env['hr.employee'].sudo().create({
                            #     'device_id_num': each.user_id,
                            #     'name': matched_user.name
                            # })

                        # Prevent duplicates
                        if not zk_attendance.sudo().search(
                                [('device_id_num', '=', each.user_id), ('punching_time', '=', atten_time)]):
                            zk_attendance.sudo().create({
                                'employee_id': employee.id,
                                'device_id_num': each.user_id,
                                'attendance_type': str(each.status),
                                'punch_type': str(each.punch),
                                'punching_time': atten_time,
                                'address_id': info.address_id.id
                            })

                    conn.disconnect()
                    self._generate_hr_attendance_from_zk_logs()
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))

    def _generate_hr_attendance_from_zk_logs(self):
        """Creates hr.attendance records using first and last ZK check-ins per employee per day."""
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']

        # Get distinct (employee, date) from zk logs
        zk_records = zk_attendance.sudo().search([], order='punching_time asc')
        attendance_dict = {}

        for record in zk_records:
            if not record.employee_id:
                continue

            employee_id = record.employee_id.id
            punch_date = fields.Date.from_string(record.punching_time)
            key = (employee_id, punch_date)

            attendance_dict.setdefault(key, []).append(record.punching_time)

        for (employee_id, date), times in attendance_dict.items():
            times = sorted([fields.Datetime.from_string(t) for t in times])

            employee = self.env['hr.employee'].sudo().browse(employee_id)

            leave = self.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee_id),
                ('state', 'in', ['validate1', 'validate']),
                ('request_date_from', '<=', date),
                ('request_date_to', '>=', date),
            ], limit=1)

            if leave:
                _logger.warning(
                    f"Skipping attendance for {employee.name} on {date} due to approved leave: {leave.holiday_status_id.name}"
                )
                continue

            # Get the resource calendar from employee's contract
            calendar = self._get_employee_calendar(employee, date)

            # Get calendar times for the day
            calendar_start = self._get_calendar_checkin_time(calendar, times[0])
            calendar_end = self._get_calendar_checkout_time(calendar, times[0])
            calendar_start -= timedelta(hours=5)
            calendar_end -= timedelta(hours=5)

            # Calculate first 4 hours from shift start
            first_four_hours_end = calendar_start + timedelta(hours=4)

            # Separate punches into first 4 hours and after
            first_four_hours_punches = [t for t in times if t <= first_four_hours_end]
            after_four_hours_punches = [t for t in times if t > first_four_hours_end]

            # Determine check_in and check_out
            auto_generated = False

            if first_four_hours_punches:
                # Use first punch in first 4 hours as check_in
                check_in = first_four_hours_punches[0]
            else:
                # No punch in first 4 hours, auto-generate check_in
                # check_in = calendar_start
                # auto_generated = True
                check_in = times[0]

            if after_four_hours_punches:
                # Use LAST punch after 4 hours as check_out (to get latest checkout)
                check_out = after_four_hours_punches[-1]
            else:
                # No punch after 4 hours, auto-generate check_out
                # check_out = calendar_end
                # auto_generated = True
                # check_out = times[-1]
                check_out = False

            # Handle open attendance from previous days
            open_attendance = hr_attendance.sudo().search([
                ('employee_id', '=', employee_id),
                ('check_out', '=', False)
            ], limit=1)

            # if open_attendance:
            #     # Auto-apply checkout to open attendance
            #     auto_checkout = self._get_calendar_checkout_time(calendar, open_attendance.check_in)
            #     auto_checkout -= timedelta(hours=5)
            #     open_attendance.write({'check_out': auto_checkout, 'auto_checkout': True})
            #     _logger.info(
            #         f"Auto-closed open attendance for employee {employee_id} with calendar checkout time")

            # Avoid duplication for the same date
            exists = hr_attendance.sudo().search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', date.strftime('%Y-%m-%d 00:00:00')),
                ('check_in', '<=', date.strftime('%Y-%m-%d 23:59:59'))
            ], limit=1)

            if exists:
                # Always update checkout if we have a real punch after 4 hours
                validated_work_entries = self.env['hr.work.entry'].sudo().search([
                    ('attendance_id', '=', exists.id),
                    ('state', '=', 'validated')
                ])
                if validated_work_entries:
                    continue
                if after_four_hours_punches:
                    # New checkout from actual punch data
                    new_checkout = after_four_hours_punches[-1]

                    # Only update if the new checkout is different (more than 30 seconds difference)
                    if not exists.check_out or abs((exists.check_out - new_checkout).total_seconds()) > 30:
                        _logger.info(f"Updating checkout time for employee {employee_id} on {date}")
                        # If we're updating with real punch data, set auto_checkout to False
                        exists.write({
                            'check_out': new_checkout,
                            # 'auto_checkout': False if first_four_hours_punches else True
                            # False only if both are real punches
                        })

                # Update check_in if the new one is earlier and from real punch
                if first_four_hours_punches and check_in < exists.check_in:
                    _logger.info(f"Updating check-in time for employee {employee_id} on {date}")
                    exists.write({
                        'check_in': check_in,
                        # 'auto_checkout': False if after_four_hours_punches else exists.auto_checkout
                    })

            else:
                # Delete any existing overtime records for this employee on this date
                existing_overtime = self.env['hr.attendance.overtime'].sudo().search([
                    ('employee_id', '=', employee_id),
                    ('date', '=', date)
                ])
                if existing_overtime:
                    existing_overtime.unlink()
                    _logger.info(f"Deleted existing overtime record for employee {employee_id} on {date}")

                # Create new attendance record
                hr_attendance.sudo().create({
                    'employee_id': employee_id,
                    'check_in': check_in,
                    'check_out': check_out,
                    # 'auto_checkout': auto_generated
                })

    # # no longer valid after the portal launch
    # def _generate_hr_attendance_from_zk_logs(self):
    #     """Creates hr.attendance records using first and last ZK check-ins per employee per day."""
    #     zk_attendance = self.env['zk.machine.attendance']
    #     hr_attendance = self.env['hr.attendance']
    #
    #     # Get distinct (employee, date) from zk logs
    #     zk_records = zk_attendance.sudo().search([], order='punching_time asc')
    #     attendance_dict = {}
    #
    #     for record in zk_records:
    #         if not record.employee_id:
    #             continue
    #
    #         employee_id = record.employee_id.id
    #         punch_date = fields.Date.from_string(record.punching_time)
    #         key = (employee_id, punch_date)
    #
    #         attendance_dict.setdefault(key, []).append(record.punching_time)
    #
    #     for (employee_id, date), times in attendance_dict.items():
    #         times = sorted([fields.Datetime.from_string(t) for t in times])
    #
    #         employee = self.env['hr.employee'].sudo().browse(employee_id)
    #
    #         leave = self.env['hr.leave'].sudo().search([
    #             ('employee_id', '=', employee_id),
    #             ('state', 'in', ['validate1', 'validate']),
    #             ('request_date_from', '<=', date),
    #             ('request_date_to', '>=', date),
    #         ], limit=1)
    #
    #         if leave:
    #             _logger.warning(
    #                 f"Skipping attendance for {employee.name} on {date} due to approved leave: {leave.holiday_status_id.name}"
    #             )
    #             continue
    #
    #         # Get the resource calendar from employee's contract
    #         calendar = self._get_employee_calendar(employee, date)
    #
    #         # Get calendar times for the day
    #         calendar_start = self._get_calendar_checkin_time(calendar, times[0])
    #         calendar_end = self._get_calendar_checkout_time(calendar, times[0])
    #         calendar_start -= timedelta(hours=5)
    #         calendar_end -= timedelta(hours=5)
    #
    #         # Calculate first 4 hours from shift start
    #         first_four_hours_end = calendar_start + timedelta(hours=4)
    #
    #         # Separate punches into first 4 hours and after
    #         first_four_hours_punches = [t for t in times if t <= first_four_hours_end]
    #         after_four_hours_punches = [t for t in times if t > first_four_hours_end]
    #
    #         # Determine check_in and check_out
    #         auto_generated = False
    #
    #         if first_four_hours_punches:
    #             # Use first punch in first 4 hours as check_in
    #             check_in = first_four_hours_punches[0]
    #         else:
    #             # No punch in first 4 hours, auto-generate check_in
    #             check_in = calendar_start
    #             auto_generated = True
    #
    #         if after_four_hours_punches:
    #             # Use LAST punch after 4 hours as check_out (to get latest checkout)
    #             check_out = after_four_hours_punches[-1]
    #         else:
    #             # No punch after 4 hours, auto-generate check_out
    #             check_out = calendar_end
    #             auto_generated = True
    #
    #         # Handle open attendance from previous days
    #         open_attendance = hr_attendance.sudo().search([
    #             ('employee_id', '=', employee_id),
    #             ('check_out', '=', False)
    #         ], limit=1)
    #
    #         if open_attendance:
    #             # Auto-apply checkout to open attendance
    #             auto_checkout = self._get_calendar_checkout_time(calendar, open_attendance.check_in)
    #             auto_checkout -= timedelta(hours=5)
    #             open_attendance.write({'check_out': auto_checkout, 'auto_checkout': True})
    #             _logger.info(
    #                 f"Auto-closed open attendance for employee {employee_id} with calendar checkout time")
    #
    #         # Avoid duplication for the same date
    #         exists = hr_attendance.sudo().search([
    #             ('employee_id', '=', employee_id),
    #             ('check_in', '>=', date.strftime('%Y-%m-%d 00:00:00')),
    #             ('check_in', '<=', date.strftime('%Y-%m-%d 23:59:59'))
    #         ], limit=1)
    #
    #         if exists:
    #             # Always update checkout if we have a real punch after 4 hours
    #             validated_work_entries = self.env['hr.work.entry'].sudo().search([
    #                 ('attendance_id', '=', exists.id),
    #                 ('state', '=', 'validated')
    #             ])
    #             if validated_work_entries:
    #                 continue
    #             if after_four_hours_punches:
    #                 # New checkout from actual punch data
    #                 new_checkout = after_four_hours_punches[-1]
    #
    #                 # Only update if the new checkout is different (more than 30 seconds difference)
    #                 if not exists.check_out or abs((exists.check_out - new_checkout).total_seconds()) > 30:
    #                     _logger.info(f"Updating checkout time for employee {employee_id} on {date}")
    #                     # If we're updating with real punch data, set auto_checkout to False
    #                     exists.write({
    #                         'check_out': new_checkout,
    #                         'auto_checkout': False if first_four_hours_punches else True
    #                         # False only if both are real punches
    #                     })
    #
    #             # Update check_in if the new one is earlier and from real punch
    #             if first_four_hours_punches and check_in < exists.check_in:
    #                 _logger.info(f"Updating check-in time for employee {employee_id} on {date}")
    #                 exists.write({
    #                     'check_in': check_in,
    #                     'auto_checkout': False if after_four_hours_punches else exists.auto_checkout
    #                 })
    #
    #         else:
    #             # Delete any existing overtime records for this employee on this date
    #             existing_overtime = self.env['hr.attendance.overtime'].sudo().search([
    #                 ('employee_id', '=', employee_id),
    #                 ('date', '=', date)
    #             ])
    #             if existing_overtime:
    #                 existing_overtime.unlink()
    #                 _logger.info(f"Deleted existing overtime record for employee {employee_id} on {date}")
    #
    #             # Create new attendance record
    #             hr_attendance.sudo().create({
    #                 'employee_id': employee_id,
    #                 'check_in': check_in,
    #                 'check_out': check_out,
    #                 'auto_checkout': auto_generated
    #             })

    def _get_employee_calendar(self, employee, date):
        """Get the resource calendar for an employee on a specific date."""
        # Try to get from active contract on the given date
        contract = self.env['hr.contract'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'open')
        ], limit=1)

        # print("CONTRACT FOUNDDD", contract , contract.resource_calendar_id.name)

        if contract and contract.resource_calendar_id:
            return contract.resource_calendar_id

        # Fallback to employee's resource calendar
        if employee.resource_calendar_id:
            return employee.resource_calendar_id

    def _get_calendar_checkin_time(self, calendar, reference_datetime):
        """Get the expected check-in time based on calendar for a given datetime."""
        if not calendar:
            # Default to 9 AM if no calendar
            return reference_datetime.replace(hour=9, minute=0, second=0, microsecond=0)

        # Get day of week (0=Monday in Odoo)
        weekday = reference_datetime.weekday()

        # Find the morning attendance line for this day
        attendance_line = calendar.attendance_ids.filtered(
            lambda a: int(a.dayofweek) == weekday and a.day_period == 'morning'
        )

        if attendance_line:
            # Get hour_from from the morning period
            hour_from = attendance_line[0].hour_from
            hours = int(hour_from)
            minutes = int((hour_from - hours) * 60)
            return reference_datetime.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        # Default to 9 AM if day not found in calendar
        return reference_datetime.replace(hour=9, minute=0, second=0, microsecond=0)

    def _get_calendar_checkout_time(self, calendar, reference_datetime):
        """Get the expected check-out time based on calendar for a given datetime."""
        if not calendar:
            return reference_datetime.replace(hour=18, minute=0, second=0, microsecond=0)

        # Get day of week (0=Monday in Odoo)
        weekday = reference_datetime.weekday()
        print("WEEKDAY", weekday)

        # Find the afternoon attendance line for this day
        attendance_line = calendar.attendance_ids.filtered(
            lambda a: int(a.dayofweek) == weekday and a.day_period == 'afternoon'
        )
        print("ATTENDANCE LINE FOUND FOR CHECKIN TIME", attendance_line, attendance_line.name)

        if attendance_line:
            # Get hour_to from the afternoon period
            hour_to = attendance_line[0].hour_to
            hours = int(hour_to)
            print("HOURS", hours)
            # minutes = int((hour_to - hours) * 60)
            return reference_datetime.replace(hour=hours, minute=0, second=0, microsecond=0)

        # Default to 6 PM if day not found in calendar
        return reference_datetime.replace(hour=18, minute=0, second=0, microsecond=0)

    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=35, password=0, force_udp=False, ommit_ping=True)
        self.device_connect(zk).restart()

    def action_download_attendance_wdms(self):
        """Fetch attendance from WDMS /iclock/api/transactions/ and store in zk.machine.attendance."""
        _logger.info("++++ WDMS Pull Started ++++")
        zk_attendance = self.env['zk.machine.attendance']
        for info in self:
            # Determine time window
            end = fields.Datetime.now()
            # start = datetime.datetime(2025, 10, 1, 0, 0, 0)
            #start = info.wdms_last_sync or (end - datetime.timedelta(minutes=20))
            params = {
                # "start_time": fields.Datetime.to_string(start).replace("T", " "),
                #"end_time": fields.Datetime.to_string(end).replace("T", " "),
                "page": 1,
                "page_size": 200,
            }
            total = 0
            while True:
                data = info._wdms_request("GET", "/iclock/api/transactions/", params=params)
                rows = data.get("data", []) if isinstance(data, dict) else []
                if not rows:
                    break

                for r in rows:
                    print("ROW ", r)
                    emp_code = (r.get("emp_code") or "").strip()
                    ptime = r.get("punch_time")  # "YYYY-MM-DD HH:MM:SS"
                    if not emp_code or not ptime:
                        continue

                    # Convert to UTC like your device path (keep behavior consistent)
                    try:
                        naive_dt = datetime.datetime.strptime(ptime, "%Y-%m-%d %H:%M:%S")
                        # local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
                        local_tz = pytz.timezone('Asia/Karachi')
                        local_dt = local_tz.localize(naive_dt, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        atten_time = fields.Datetime.to_string(
                            datetime.datetime.strptime(utc_dt.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
                        )
                    except Exception:
                        atten_time = ptime  # fallback (already proper fmt)

                    # Find/Create employee by device_id_num
                    employee = self.env['hr.employee'].sudo().search([('device_id_num', '=', emp_code)], limit=1)
                    if not employee:
                        continue
                        # employee = self.env['hr.employee'].sudo().create({
                        #     'device_id_num': emp_code,
                        #     'name': f"{emp_code}"
                        # })

                    # De-dup (like your device path): device_id_num + punching_time
                    dup = zk_attendance.sudo().search([
                        ('device_id_num', '=', emp_code),
                        ('punching_time', '=', atten_time)
                    ], limit=1)
                    if dup:
                        continue

                    zk_attendance.sudo().create({
                        'employee_id': employee.id,
                        'device_id_num': emp_code,
                        'attendance_type': str(r.get("verify_type") or '1'),
                        'punch_type': '0' if str(r.get("punch_state")) == '0' else '1',  # basic IN/OUT
                        'punching_time': atten_time,
                        'address_id': info.address_id.id
                    })
                    total += 1

                if len(rows) < params["page_size"]:
                    break
                params["page"] += 1

            info.sudo().write({"wdms_last_sync": end})
            _logger.info("++++ WDMS Pull Completed for %s, created=%s ++++", info.display_name, total)

        # Generate hr.attendance from ZK logs (reuse your existing method)
        self._generate_hr_attendance_from_zk_logs()
        return True

    @api.model
    def cron_download_attendance_for_device_name(self, device_name):
        """Cron job method to download attendance for a specific device by name"""
        context = dict(self.env.context, tz='Asia/Karachi')
        device = self.with_context(context).search([('name', '=', device_name)], limit=1)
        if device and device.name == 'Lahore New':
            device.action_download_attendance_wdms()
        else:
            device.action_download_attendance()

    # def _generate_hr_attendance_from_zk_logs(self):
    #     """Creates hr.attendance records using first and last ZK check-ins per employee per day."""
    #     zk_attendance = self.env['zk.machine.attendance']
    #     hr_attendance = self.env['hr.attendance']
    #
    #     # Get distinct (employee, date) from zk logs
    #     zk_records = zk_attendance.sudo().search([], order='punching_time asc')
    #     attendance_dict = {}
    #
    #     for record in zk_records:
    #         if not record.employee_id:
    #             continue
    #
    #         employee_id = record.employee_id.id
    #         punch_date = fields.Date.from_string(record.punching_time)
    #         key = (employee_id, punch_date)
    #
    #         attendance_dict.setdefault(key, []).append(record.punching_time)
    #
    #     for (employee_id, date), times in attendance_dict.items():
    #         times = sorted([fields.Datetime.from_string(t) for t in times])
    #         check_in = times[0]
    #         check_out = times[-1]
    #
    #         employee = self.env['hr.employee'].sudo().browse(employee_id)
    #         # contract = self.env['hr.contract'].search([
    #         #     ('employee_id', '=', employee_id),
    #         #     ('state', '=', 'open')
    #         # ], limit=1)
    #         #
    #         # if not contract:
    #         #     _logger.warning(f"Skipping {employee.name} (no active contract)")
    #         #     continue
    #
    #         leave = self.env['hr.leave'].sudo().search([
    #             ('employee_id', '=', employee_id),
    #             ('state', 'in', ['validate1','validate']),
    #             ('request_date_from', '<=', date),
    #             ('request_date_to', '>=', date),
    #         ], limit=1)
    #
    #         if leave:
    #             _logger.warning(
    #                 f"Skipping attendance for {employee.name} on {date} due to approved leave: {leave.holiday_status_id.name}"
    #             )
    #             continue
    #
    #         # Get the resource calendar from employee's contract
    #         calendar = self._get_employee_calendar(employee, date)
    #
    #         # Handle open attendance from previous days
    #         open_attendance = hr_attendance.sudo().search([
    #             ('employee_id', '=', employee_id),
    #             ('check_out', '=', False)
    #         ], limit=1)
    #
    #         if open_attendance:
    #             print("IN OPEN ATTENDANCE CONDITION")
    #             previous_check_in = open_attendance.check_in
    #             previous_date = fields.Date.from_string(previous_check_in)
    #
    #             # Only auto-close if it's from a previous day
    #             # if previous_date < date:
    #             if check_in > previous_check_in:
    #                 # Get checkout time from calendar for the previous day
    #                 auto_checkout = self._get_calendar_checkout_time(calendar, previous_check_in)
    #                 print("CHECKOUT AUTO TIME", auto_checkout)
    #                 open_attendance.write({'check_out': auto_checkout})
    #                 _logger.info(
    #                     f"Auto-closed attendance for employee {employee_id} on {previous_date} with calendar checkout time")
    #
    #         # Avoid duplication for the same date
    #         exists = hr_attendance.sudo().search([
    #             ('employee_id', '=', employee_id),
    #             ('check_in', '>=', date.strftime('%Y-%m-%d 00:00:00')),
    #             ('check_in', '<=', date.strftime('%Y-%m-%d 23:59:59'))
    #         ], limit=1)
    #
    #         if exists:
    #             # Update existing record if we have better data
    #             # Check if the existing checkout was auto-generated (matches calendar time)
    #             calendar_end = self._get_calendar_checkout_time(calendar, exists.check_in)
    #             calendar_end -= timedelta(hours=5)
    #
    #             # If existing checkout is the calendar time (auto-generated) and we have actual punch data
    #             if exists.check_out and check_out != check_in:
    #                 # Check if existing checkout matches calendar time (within 1 minute tolerance)
    #                 time_diff = abs((exists.check_out - calendar_end).total_seconds())
    #                 if time_diff < 5:  # Within 1 minute means it was auto-generated
    #                     _logger.info(f"Updating auto-generated checkout for employee {employee_id} on {date}")
    #                     exists.write({'check_out': check_out, 'auto_checkout': False})
    #                 else:
    #                     # Real checkout exists, check if new one is different
    #                     if abs((exists.check_out - check_out).total_seconds()) > 30:
    #                         _logger.info(f"Updating checkout time for employee {employee_id} on {date}")
    #                         exists.write({'check_out': check_out, 'auto_checkout': False})
    #
    #             # Also update check_in if the new one is earlier
    #             if check_in < exists.check_in:
    #                 _logger.info(f"Updating check-in time for employee {employee_id} on {date}")
    #                 exists.write({'check_in': check_in})
    #
    #         else:
    #             # Delete any existing overtime records for this employee on this date
    #             existing_overtime = self.env['hr.attendance.overtime'].sudo().search([
    #                 ('employee_id', '=', employee_id),
    #                 ('date', '=', date)
    #             ])
    #             if existing_overtime:
    #                 existing_overtime.unlink()
    #                 _logger.info(f"Deleted existing overtime record for employee {employee_id} on {date}")
    #
    #             # If only one punch on the day, determine if it's check-in or check-out
    #             if check_in == check_out:
    #                 print("IN CHECKIN AND CHECK OUT CONDITION")
    #                 # Single punch - need to determine if it's IN or OUT based on calendar
    #                 print("CALLING CHECK IN AND CHECKOUT FUNCTIONS FROM EXISTS CONDITION")
    #                 calendar_start = self._get_calendar_checkin_time(calendar, check_in)
    #                 calendar_end = self._get_calendar_checkout_time(calendar, check_in)
    #                 print("calendar_start", calendar_start)
    #                 print("calendar_end", calendar_end)
    #
    #                 calendar_start -= timedelta(hours=5)
    #                 calendar_end -= timedelta(hours=5)
    #
    #                 # If punch is closer to start time, treat as check-in
    #                 # If closer to end time, treat as check-out
    #                 time_diff_start = abs((check_in - calendar_start).total_seconds())
    #                 time_diff_end = abs((check_in - calendar_end).total_seconds())
    #
    #                 if time_diff_start < time_diff_end:
    #                     # It's a check-in, add calendar checkout
    #                     hr_attendance.sudo().create({
    #                         'employee_id': employee_id,
    #                         'check_in': check_in,
    #                         'check_out': calendar_end,
    #                         'auto_checkout': True
    #                     })
    #                 else:
    #                     # It's a check-out, add calendar checkin
    #                     hr_attendance.sudo().create({
    #                         'employee_id': employee_id,
    #                         'check_in': calendar_start,
    #                         'check_out': check_in,
    #                         'auto_checkout': False,
    #                     })
    #             else:
    #                 # Multiple punches - use first and last
    #                 hr_attendance.sudo().create({
    #                     'employee_id': employee_id,
    #                     'check_in': check_in,
    #                     'check_out': check_out if check_out > check_in else False,
    #                     'auto_checkout': False,
    #                 })
