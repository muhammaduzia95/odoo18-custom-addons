from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    applicant_id = fields.Many2one(
        'res.partner',
        string="Applicant",
        domain="[('parent_id', '=', partner_id)]"
    )

    project_tags = fields.Many2many('po.project.tags' , string="Project Tags")

    can_create_bill = fields.Boolean(
        string='Can Create Bill',
        store=True,
        help='Technical field to control Create Bill button visibility'
    )

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        result = super(StockPicking, self).button_validate()

        for picking in self:
            if picking.location_dest_id.name == 'Stock':
                print("IN STOCK CONDITION")

                if picking.group_id and picking.group_id.name:
                    po_name = picking.group_id.name
                    print(f"PO name from group: {po_name}")

                    po = self.env['purchase.order'].search([('name', '=', po_name)], limit=1)

                    if po:
                        print(f"Found PO: {po.name}")
                        po.sudo().write({'can_create_bill': True})
                        print("Updated can_create_bill to True")
                    else:
                        print(f"No PO found with name: {po_name}")
                else:
                    print("No group_id or group_id.name found")

        return result