from odoo import http
from odoo.http import request, Response
import json
import logging
from datetime import datetime
import pytz

_logger = logging.getLogger(__name__)

class DeviceAttendanceAPI(http.Controller):

    @http.route('/api/amt_device_log', type='json', auth='public', methods=['POST'], csrf=False)
    def store_device_log(self, **post):
        try:
            _logger.info(f"Received JSON Payload: {post}")

            amt_seq_id = post.get('amt_seq_id')
            device_user_id = post.get('device_user_id')
            device_id_num = post.get('device_id_num')
            punching_time_str = post.get('punching_time')

            # if not device_user_id or not punching_time_str or not amt_seq_id:
            #     return Response(
            #         json.dumps({
            #             "status": "error",
            #             "message": "Missing required fields: 'amt_seq_id', 'device_user_id', or 'punching_time'"
            #         }),
            #         status=400,
            #         content_type='application/json'
            #     )
            #
            # local_tz = pytz.timezone('Asia/Karachi')
            # naive_dt = datetime.strptime(punching_time_str, '%Y-%m-%d %H:%M:%S')
            # local_dt = local_tz.localize(naive_dt)
            # utc_dt = local_dt.astimezone(pytz.utc)

            request.env['device.attendance'].sudo().create({
                'name': f"{amt_seq_id} - {device_user_id} - {device_id_num}",
                'amt_seq_id': amt_seq_id,
                'device_user_id': device_user_id,
                'device_id_num': device_id_num,
                'punching_time': punching_time_str,
            })

            return Response(
                json.dumps({
                    "status": "success",
                    "message": "Attendance log saved successfully"
                }),
                status=200,
                content_type='application/json'
            )

        except Exception as e:
            _logger.exception("Error processing attendance log")
            return Response(
                json.dumps({
                    "status": "error",
                    "message": str(e)
                }),
                status=500,
                content_type='application/json'
            )
