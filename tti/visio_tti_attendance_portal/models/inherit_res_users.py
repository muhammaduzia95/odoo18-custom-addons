# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_hr_customize\models\inherit_res_users.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = "res.users"

    marketing_attendance_portal_access = fields.Boolean(
        string="Access Marketing Attendance Portal Users")

    manager_approval_portal_access = fields.Boolean(
        string="Access Manager Approval Portal")

    def _sync_marketing_attendance_group(self):
        group = self.env.ref(
            "visio_tti_attendance_portal.group_marketing_attendance_portal",
            raise_if_not_found=False
        )
        if not group:
            return

        for user in self.sudo():
            # only makes sense for portal users
            if not user.share:
                continue

            if user.marketing_attendance_portal_access:
                user.write({"groups_id": [(4, group.id)]})  # add
            else:
                user.write({"groups_id": [(3, group.id)]})  # remove

    def _sync_manager_approval_portal_group(self):
        group = self.env.ref(
            "visio_tti_attendance_portal.group_manager_approval_portal",
            raise_if_not_found=False
        )
        if not group:
            return

        for user in self.sudo():
            # NOTE: don't check user.share here (managers are usually internal users)
            if user.manager_approval_portal_access:
                user.write({"groups_id": [(4, group.id)]})  # add
            else:
                user.write({"groups_id": [(3, group.id)]})  # remove

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._sync_marketing_attendance_group()
        users._sync_manager_approval_portal_group()
        return users

    def write(self, vals):
        res = super().write(vals)
        if "marketing_attendance_portal_access" in vals:
            self._sync_marketing_attendance_group()
        if "manager_approval_portal_access" in vals:
            self._sync_manager_approval_portal_group()
        return res
