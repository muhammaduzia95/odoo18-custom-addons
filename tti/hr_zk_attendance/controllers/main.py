# D:\Visiomate\Odoo\odoo18\custom_addons\tti\hr_zk_attendance\controllers\main.py


from odoo.http import Controller, route, request, Response
from odoo import fields
from odoo.exceptions import ValidationError
import logging
import pytz
from datetime import datetime
import json

_logger = logging.getLogger(__name__)


class AttendanceAPI(Controller):

    @route('/api/amt_attendance', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_attendance(self, **kwargs):
        try:
            _logger.info(f":::: AMT Attendance API :::: AMT Machine Payload :::: {kwargs}")
            device_id = kwargs.get('device_id_num')
            user_id = kwargs.get('device_user_id')
            punch_type = '0'
            attendance_type = '1'
            punch_time = kwargs.get('punching_time')

            if not user_id or not punch_time:
                return Response(
                    json.dumps({
                        "status": "error",
                        "message": "Missing required fields: 'device_user_id' or 'punching_time'"
                    }),
                    status=400,
                    content_type='application/json'
                )

            try:
                naive_dt = datetime.strptime(punch_time, '%Y-%m-%d %H:%M:%S')
                local_tz = pytz.timezone('Asia/Karachi')
                local_dt = local_tz.localize(naive_dt, is_dst=None)
                utc_dt = local_dt.astimezone(pytz.utc)
                punch_time_dt = utc_dt.replace(tzinfo=None)
            except Exception as e:
                _logger.error("Datetime parse error: %s", str(e))
                return Response(
                    json.dumps({
                        "status": "error",
                        "message": "Invalid datetime format. Use 'YYYY-MM-DD HH:MM:SS'"
                    }),
                    status=400,
                    content_type='application/json'
                )

            employee = request.env['hr.employee'].sudo().search([('device_id_num', '=', user_id)], limit=1)
            if not employee:
                employee = request.env['hr.employee'].sudo().create({
                    'device_id_num': user_id,
                    'name': f"{user_id} - {device_id}",
                })

            zk_attendance = request.env['zk.machine.attendance']
            biometric_device_details = request.env['biometric.device.details'].sudo().search(
                [('device_ip', '=', "/api/amt_attendance")], limit=1)
            address_id = biometric_device_details.address_id.id if biometric_device_details else False

            vals = {
                'employee_id': employee.id,
                'device_id_num': device_id,
                'punch_type': punch_type,
                'punching_time': punch_time_dt,
                'attendance_type': attendance_type,
                'address_id': address_id,
            }

            _logger.info(f":::: AMT Attendance API :::: Attendance Payload :::: {vals}")

            if not zk_attendance.sudo().search(
                    [('device_id_num', '=', device_id), ('punching_time', '=', punch_time_dt)]):
                zk_record = zk_attendance.sudo().create(vals)
                _logger.info(f":::: zk.machine.attendance Created :::: {zk_record}")

                # --- Trigger hr.attendance generation for this employee and date ---
                punch_date = fields.Date.from_string(punch_time_dt.strftime('%Y-%m-%d'))
                employee_id = employee.id

                # Collect all zk punches for the same employee on that day
                records = zk_attendance.sudo().search([
                    ('employee_id', '=', employee_id),
                    ('punching_time', '>=', punch_date.strftime('%Y-%m-%d 00:00:00')),
                    ('punching_time', '<=', punch_date.strftime('%Y-%m-%d 23:59:59')),
                ], order='punching_time asc')

                if records:
                    check_in = records[0].punching_time
                    check_out = records[-1].punching_time

                    hr_attendance = request.env['hr.attendance']

                    # First close any open attendance
                    open_attendance = hr_attendance.sudo().search([
                        ('employee_id', '=', employee_id),
                        ('check_out', '=', False)
                    ], limit=1)

                    if open_attendance:
                        if check_in > open_attendance.check_in:
                            open_attendance.write({'check_out': check_in})
                        else:
                            _logger.warning(
                                f"Skipped closing attendance for employee {employee_id} due to invalid sequence.")

                    # Avoid duplicate hr.attendance
                    exists = hr_attendance.sudo().search([
                        ('employee_id', '=', employee_id),
                        ('check_in', '>=', punch_date.strftime('%Y-%m-%d 00:00:00')),
                        ('check_in', '<=', punch_date.strftime('%Y-%m-%d 23:59:59'))
                    ], limit=1)

                    if not exists:
                        hr_attendance.sudo().create({
                            'employee_id': employee_id,
                            'check_in': check_in,
                            'check_out': check_out if check_out > check_in else False,
                        })

            return Response(
                json.dumps({
                    "status": "success",
                    "message": "Attendance recorded and hr.attendance updated"
                }),
                status=200,
                content_type='application/json'
            )

        except ValidationError as ve:
            _logger.error("Validation error: %s", ve)
            return Response(
                json.dumps({
                    "status": "error",
                    "message": str(ve)
                }),
                status=422,
                content_type='application/json'
            )

        except Exception as e:
            _logger.exception("Internal server error")
            return Response(
                json.dumps({
                    "status": "error",
                    "message": "Internal Server Error: " + str(e)
                }),
                status=500,
                content_type='application/json'
            )

#     @route('/api/amt_attendance', type='json', auth='public', methods=['POST'], csrf=False)
#     def receive_attendance(self, **kwargs):
#         try:
#             _logger.info(f":::: AMT Attendance API :::: AMT Machine Payload :::: {kwargs}")
#             device_id = kwargs.get('device_id_num')
#             user_id = kwargs.get('device_user_id')
#             punch_type = '0'
#             attendance_type = '1'
#             punch_time = kwargs.get('punching_time')
#
#             # Validate required fields
#             if not user_id or not punch_time:
#                 return Response(
#                     json.dumps({
#                         "status": "error",
#                         "message": "Missing required fields: 'device_user_id' or 'punching_time'"
#                     }),
#                     status=400,
#                     content_type='application/json'
#                 )
#
#             try:
#                 naive_dt = datetime.strptime(punch_time, '%Y-%m-%d %H:%M:%S')
#                 local_tz = pytz.timezone('Asia/Karachi')  # or get from request.env.user.partner_id.tz
#                 local_dt = local_tz.localize(naive_dt, is_dst=None)
#                 utc_dt = local_dt.astimezone(pytz.utc)
#                 punch_time_dt = utc_dt.replace(tzinfo=None)
#
#             except Exception as e:
#                 _logger.error("Datetime parse error: %s", str(e))
#                 return Response(
#                     json.dumps({
#                         "status": "error",
#                         "message": "Invalid datetime format. Use 'YYYY-MM-DD HH:MM:SS'"
#                     }),
#                     status=400,
#                     content_type='application/json'
#                 )
#
#
#             # Lookup employee
#             employee = request.env['hr.employee'].sudo().search([('device_id_num', '=', user_id)], limit=1)
#             if not employee:
#                 _logger.error(f"Employee not found for device_user_id: {user_id}")
#                 # return Response(
#                 #     json.dumps({
#                 #         "status": "error",
#                 #         "message": f"Employee not found for device_user_id: {user_id}"
#                 #     }),
#                 #     status=404,
#                 #     content_type='application/json'
#                 # )
#                 if not employee:
#                     employee = request.env['hr.employee'].sudo().create({
#                         'device_id_num': user_id,
#                         'name': f"{user_id} - {device_id}",
#                     })
#
#             zk_attendance = request.env['zk.machine.attendance']
#             address_id = False
#             biometric_device_details = request.env['biometric.device.details'].sudo().search([('device_ip', '=', "/api/amt_attendance")], limit=1)
#             if biometric_device_details:
#                 address_id = biometric_device_details.address_id
#
#             vals = {
#                 'employee_id': employee.id,
#                 'device_id_num': device_id,
#                 'punch_type': punch_type,
#                 'punching_time': punch_time_dt,
#                 'attendance_type': attendance_type,
#                 'address_id': address_id.id if address_id else False,
#             }
#             _logger.info(f":::: AMT Attendance API :::: Attendance Payload :::: {vals}")
#             # Prevent duplicates
#             if not zk_attendance.sudo().search([('device_id_num', '=', device_id), ('punching_time', '=', punch_time_dt)]):
#                 zk_machine_attendance = zk_attendance.sudo().create(vals)
#                 if zk_machine_attendance:
#                     # request.env['biometric.device.details'].sudo()._generate_hr_attendance_from_zk_logs()
#                     _logger.info(f":::: zk.machine.attendance :::: payload :::: {zk_machine_attendance}")
#
#             return Response(
#                 json.dumps({
#                     "status": "success",
#                     "message": "Attendance recorded successfully"
#                 }),
#                 status=200,
#                 content_type='application/json'
#             )
#
#         except ValidationError as ve:
#             _logger.error("Validation error: %s", ve)
#             return Response(
#                 json.dumps({
#                     "status": "error",
#                     "message": str(ve)
#                 }),
#                 status=422,
#                 content_type='application/json'
#             )
#
#         except Exception as e:
#             _logger.exception("Internal server error")
#             return Response(
#                 json.dumps({
#                     "status": "error",
#                     "message": "Internal Server Error: " + str(e)
#                 }),
#                 status=500,
#                 content_type='application/json'
#             )
