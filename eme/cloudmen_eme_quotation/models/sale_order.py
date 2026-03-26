from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # show_model_in_reports = fields.Boolean(string = 'Show Models in Reports', default=True) #zia comment
    # show_brand_in_reports = fields.Boolean(string = 'Show Brand in Reports', default=True) #zia comment

    # consultant_id = fields.Many2one(
    #     'res.partner',
    #     string='Consultant',
    #     compute='_compute_consultant_id',
    #     readonly=False,
    #     store=True
    # )

    consultant_id = fields.Many2one(
        'res.partner',
        string='Consultant',
        readonly=False,
        store=True
    )

    attention_id = fields.Many2one(
        'res.partner',
        string='Attention',
        compute='_compute_attention_id',
        store=True,
        readonly=False
    )
    subject = fields.Char(string='Subject', readonly=False, store=True)

    details = fields.Text(string="Details")

    @api.depends('partner_id')
    def _compute_attention_id(self):
        for record in self:
            if not record.partner_id.is_company:
                record.attention_id = record.partner_id
            else:
                record.attention_id = False

    # @api.depends('opportunity_id')
    # def _compute_consultant_id(self):
    #     for record in self:
    #         record.consultant_id = record.opportunity_id.x_studio_consultant

    # zia comment
    # def get_section_total(self, section_line):
    #     """Compute the total price for all lines after this section until another section appears."""
    #     total = 0.0
    #     start_counting = False
    #     for line in self.order_line:
    #         if line.id == section_line.id:
    #             start_counting = True
    #             continue
    #         if start_counting and line.display_type in ['line_section']:
    #             break
    #         if start_counting:
    #             total += line.price_subtotal
    #     return total
