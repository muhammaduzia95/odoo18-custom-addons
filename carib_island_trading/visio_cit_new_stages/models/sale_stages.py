# D:\Visiomate\Odoo\odoo18\custom_addons\carib_island_trading\visio_cit_new_stages\models\sale_stages.py
from odoo import models, fields

class SaleStages(models.Model):
    _name = 'sale.stages'
    _description = 'Sale Stages'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer(string="Sequence")
    fold = fields.Boolean(string='Folded in Statusbar', default=False)
