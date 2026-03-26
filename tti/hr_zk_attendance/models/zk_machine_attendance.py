# D:\Visiomate\Odoo\odoo18\custom_addons\tti\hr_zk_attendance\models\zk_machine_attendance.py


# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime


class ZkMachineAttendance(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'zk.machine.attendance'
    _description = 'Attendance'
    _inherit = 'hr.attendance'

    # @api.constrains('check_in', 'check_out', 'employee_id')
    # def _check_validity(self):
    #     """Overriding the __check_validity function for employee attendance."""
    #     pass
    #
    # @api.constrains('check_in', 'check_out', 'employee_id')
    # def _check_validity(self):
    #     """ Verifies the validity of the attendance record compared to the others from the same employee.
    #         For the same employee we must have :
    #             * maximum 1 "open" attendance record (without check_out)
    #             * no overlapping time slices with previous employee records
    #     """
    #     for attendance in self:
    #         # we take the latest attendance before our check_in time and check it doesn't overlap with ours
    #         last_attendance_before_check_in = self.env['hr.attendance'].search([
    #             ('employee_id', '=', attendance.employee_id.id),
    #             ('check_in', '<=', attendance.check_in),
    #             ('id', '!=', attendance.id),
    #         ], order='check_in desc', limit=1)
    #         if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
    #             raise exceptions.ValidationError(
    #                 _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
    #                     'empl_name': attendance.employee_id.name,
    #                     'datetime': format_datetime(self.env, attendance.check_in, dt_format=False),
    #                 })
    #
    #         if not attendance.check_out:
    #             # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
    #             no_check_out_attendances = self.env['hr.attendance'].search([
    #                 ('employee_id', '=', attendance.employee_id.id),
    #                 ('check_out', '=', False),
    #                 ('id', '!=', attendance.id),
    #             ], order='check_in desc', limit=1)
    #             if no_check_out_attendances:
    #                 # raise exceptions.ValidationError(
    #                 #     _("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
    #                 #         'empl_name': attendance.employee_id.name,
    #                 #         'datetime': format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False),
    #                 #     })
    #                 pass
    #         else:
    #             # we verify that the latest attendance with check_in time before our check_out time
    #             # is the same as the one before our check_in time computed before, otherwise it overlaps
    #             last_attendance_before_check_out = self.env['hr.attendance'].search([
    #                 ('employee_id', '=', attendance.employee_id.id),
    #                 ('check_in', '<', attendance.check_out),
    #                 ('id', '!=', attendance.id),
    #             ], order='check_in desc', limit=1)
    #             if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
    #                 raise exceptions.ValidationError(
    #                     _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
    #                         'empl_name': attendance.employee_id.name,
    #                         'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in,
    #                                                     dt_format=False),
    #                     })

    device_id_num = fields.Char(string='Biometric Device ID', help="The ID of the Biometric Device")
    punch_type = fields.Selection([('0', 'Check In'), ('1', 'Check Out'),
                                   ('2', 'Break Out'), ('3', 'Break In'),
                                   ('4', 'Overtime In'), ('5', 'Overtime Out'),
                                   ('255', 'Duplicate')],
                                  string='Punching Type',
                                  help='Punching type of the attendance')
    attendance_type = fields.Selection([
        ('1', 'Finger'),
        ('2', 'Type_2'),
        ('3', 'Password'),
        ('4', 'Card'),
        ('15', 'Face'),
        ('16', 'Type_16'),
    ], string='Category', help='Attendance detecting methods')
    punching_time = fields.Datetime(string='Punching Time', help="Punching time in the device")
    address_id = fields.Many2one('res.partner', string='Working Address', help="Working address of the employee")


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(
                    _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                        'empl_name': attendance.employee_id.name,
                        'datetime': format_datetime(self.env, attendance.check_in, dt_format=False),
                    })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if no_check_out_attendances:
                    # raise exceptions.ValidationError(
                    #     _("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                    #         'empl_name': attendance.employee_id.name,
                    #         'datetime': format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False),
                    #     })
                    pass
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    raise exceptions.ValidationError(
                        _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                            'empl_name': attendance.employee_id.name,
                            'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in,
                                                        dt_format=False),
                        })