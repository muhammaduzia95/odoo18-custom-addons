# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_out_sourced\models\out_sourced_sample.py
from odoo import models, fields


class OutSourcedSample(models.Model):
    _name = 'out.sourced.sample'
    _description = 'Out Sourced Sample'

    name = fields.Char(string="Sample Name", required=True)
