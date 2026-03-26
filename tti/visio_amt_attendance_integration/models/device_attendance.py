from odoo import models, fields

class DeviceAttendance(models.Model):
    _name = 'device.attendance'
    _description = 'Raw Device Attendance Data'
    _order = 'id DESC'

    name = fields.Char(string='Name')
    amt_seq_id = fields.Char(string='AMT Device Sequence ID')
    device_user_id = fields.Char(string='Device User ID')
    device_id_num = fields.Char(string='Device ID Number')
    punching_time = fields.Char(string='Punching Time')
