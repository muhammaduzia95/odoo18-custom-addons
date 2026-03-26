from odoo import models, fields, api


class ProjectTags(models.Model):
    _name = 'po.project.tags'
    _description = 'Project Tags'

    name = fields.Char(string='Name', required=True)