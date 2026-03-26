from odoo import models, fields

class SoPackageDifferenceWizard(models.TransientModel):
    _name = 'so.package.difference.wizard'
    _description = 'SO Package Difference Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    def action_print_report(self):
        data = {
            'date_from': self.date_from.strftime('%Y-%m-%d'),
            'date_to': self.date_to.strftime('%Y-%m-%d'),
        }
        return self.env.ref('visio_tti_so_customize.report_so_package_difference_excel').report_action(self, data=data)
