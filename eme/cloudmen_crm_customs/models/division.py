from odoo import models, fields, api


class Division(models.Model):
    _name = 'x.division'  # Fixed: Should use underscores, not asterisks
    _description = 'Division'
    _rec_name = 'name'  # Fixed: Should use underscores, not asterisks

    name = fields.Char('Division Name', required=True)
    code = fields.Char('Division Code')
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [  # Fixed: Should use underscores, not asterisks
        ('name_unique', 'UNIQUE(name)', 'Division name must be unique!'),
        ('code_unique', 'UNIQUE(code)', 'Division code must be unique!'),
    ]