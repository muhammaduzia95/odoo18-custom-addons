from odoo import models, fields , api

class PurchaseStages(models.Model):
    _name = 'purchase.stages'
    _description = 'Purchase Stages'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer(string="Sequence")
    fold = fields.Boolean(string='Folded in Statusbar', default=False)
