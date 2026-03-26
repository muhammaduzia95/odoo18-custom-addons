from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dept_id = fields.Char(string="Department" , compute="_compute_department", store=True)

    @api.depends('partner_id')
    def _compute_department(self):
        for picking in self:
            if picking.partner_id:
                employee = picking.partner_id.employee_ids[:1]
                if employee:
                    department = employee.department_id.name if employee.department_id else ''
                    picking.dept_id = department
                else:
                    picking.dept_id = False

    report_button = fields.Char(
        compute='_compute_report_button',
        help="Determines which report buttons to show based on sequence_code."
    )

    vehicle_number = fields.Char(
        string='Vehicle Number'
    )

    @api.depends('picking_type_id.sequence_code')
    def _compute_report_button(self):
        for picking in self:
            sequence_code = picking.picking_type_id.sequence_code or ''
            if sequence_code == 'GIN':
                picking.report_button = 'gin'
            elif sequence_code == 'IGP':
                picking.report_button = 'igp'
            elif sequence_code == 'GRN':
                picking.report_button = 'grn'
            else:
                picking.report_button = ''
