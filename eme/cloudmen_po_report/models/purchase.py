from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    delivery_partner_id = fields.Many2one('res.partner', string="Delivery Contact")
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.company.country_id.id)
    state_id = fields.Many2one(
        "res.country.state", string='State',
        domain="[('country_id', '=?', country_id)]")
    po_project_id = fields.Many2one('project.project', string="Project")
