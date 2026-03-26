
from odoo import models, fields, api


class ApiLog(models.Model):
    _name = 'ektefa.api.log'
    _description = 'Ektefa API Log'
    _order = 'id DESC'
    _check_company_auto = True

    name = fields.Char(string="Request Name", required=True)
    request_data = fields.Text(string="Request Data")
    response_data = fields.Text(string="Response Data")
    request_timestamp = fields.Datetime(string="Request Timestamp", default=fields.Datetime.now)
    response_timestamp = fields.Datetime(string="Response Timestamp")
    status = fields.Selection([
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], string="Status", required=True)
    error_message = fields.Text(string="Error Message")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, list_vals):
        for vals in list_vals:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
        return super(ApiLog, self).create(list_vals)

    def write(self, vals):
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        return super(ApiLog, self).write(vals)
