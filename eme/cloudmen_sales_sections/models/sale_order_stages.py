from odoo import models, fields


class SaleOrderStageCategory(models.Model):
    _name = 'sale.order.stage.categ'

    name = fields.Char(string="Name")


class SaleOrderStage(models.Model):
    _name = 'sale.order.stage'
    _description = 'Sale Order Stage'
    _log_access = True
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string = 'Name', readonly=False, store=True)
    category_id = fields.Many2one('sale.order.stage.categ', string="Category")
    description = fields.Html(string='Description', help="Stage Description")
