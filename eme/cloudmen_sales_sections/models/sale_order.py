from odoo import models, fields
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from dateutil import relativedelta


from odoo.tools import format_amount, format_date, format_datetime, pdf


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    show_pricing_in_report = fields.Boolean(string='Show Pricing In Reports', default=True)
    stage_from = fields.Many2one('sale.order.stage', string = 'Stage From')
    stage_to = fields.Many2one('sale.order.stage', string = 'Stage To')

    stage_categ_ids = fields.Many2many('sale.order.stage.categ')
    order_stage_ids = fields.Many2many('sale.order.stage', compute="_compute_stage_ids", store=True)



    description = fields.Html(string='Description', help="Stage Description")

    @api.depends('stage_categ_ids')
    def _compute_stage_ids(self):
        for rec in self:
            rec.order_stage_ids = [(5,0,0)]
            if rec.stage_categ_ids:
                stages = self.env['sale.order.stage'].search([('category_id', 'in', rec.stage_categ_ids.ids)])
                rec.order_stage_ids = [(4, stage_id) for stage_id in stages.ids]



    @api.onchange('order_stage_ids')
    def set_default_stages(self):
        for order in self:
            desc = ''
            for stage in order.order_stage_ids:
                desc += stage.description
            order.description = desc
