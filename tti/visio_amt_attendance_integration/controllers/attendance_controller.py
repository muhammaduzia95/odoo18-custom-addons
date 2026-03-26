from odoo import http
from odoo.http import request, Response
import json
import logging
from datetime import datetime
import pytz

_logger = logging.getLogger(__name__)

class DeviceAttendanceWebhook(http.Controller):

    @http.route('/api/amt_device_log', type='json', auth='public', methods=['POST', 'GET'], csrf=False)
    def receive_device_log(self, **post):
        """
        Webhook endpoint for receiving device attendance logs.
        Expects JSON payload with:
        - amt_seq_id
        - device_user_id
        - device_id_num
        - punching_time (ISO format preferred: 'YYYY-MM-DDTHH:MM:SS')
        """
        try:
            _logger.error(f"[Webhook] Received payload: {post}")
            _logger.info(f"[Webhook] Received payload: {json.dumps(post)}")

            # Extract data
            amt_seq_id = post.get('amt_seq_id')
            device_user_id = post.get('device_user_id')
            device_id_num = post.get('device_id_num')
            punching_time_str = post.get('punching_time')

            if not all([amt_seq_id, device_user_id, device_id_num, punching_time_str]):
                raise ValueError("Missing required fields in the payload")

            # Optional: Parse punching_time to UTC datetime
            punching_time = datetime.fromisoformat(punching_time_str)
            utc = pytz.UTC
            punching_time = punching_time.astimezone(utc)

            # Create attendance record
            request.env['device.attendance'].sudo().create({
                'name': f"{amt_seq_id} - {device_user_id} - {device_id_num}",
                'amt_seq_id': amt_seq_id,
                'device_user_id': device_user_id,
                'device_id_num': device_id_num,
                'punching_time': punching_time,
            })

            return Response(
                json.dumps({"status": "success", "message": "Attendance log saved"}),
                status=200,
                content_type='application/json'
            )

        except Exception as e:
            _logger.exception("[Webhook] Failed to process device log")
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=200,  # Still return 200 to avoid webhook retries if you handle it gracefully
                content_type='application/json'
            )
