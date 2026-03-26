# quran_academy\visio_contact_extension_qa\wizard\lables_list_wizard.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LablesListWizard(models.TransientModel):
    _name = 'lables.list.wizard'
    _description = 'Lables List Wizard'

    qa_gender = fields.Selection([
        ('m', 'M'),
        ('f', 'F'),
        ('o', 'Other')
    ], string="Gender", default='m')

    qa_type_contact = fields.Selection([
        ('default', 'Default'),
        ('mohsinin', 'Mohsinin'),
        ('permanent', 'Permanent'),
        ('general', 'General')
    ], string="Type of Contact", default='general')

    print_type = fields.Selection([
        ('mohsineen', 'Lables Mohsineen'),
        ('by_hand', 'By Hand List'),
    ], string="Lables/List", required=True, default='mohsineen')

    def action_generate_report(self):
        print("Wizard triggered")

        # Start with base filter: only active labels
        domain = [('label_hold_yn', '=', False)]

        # Add gender filter only if selected
        if self.qa_gender:
            domain.append(('gender_qa', '=', self.qa_gender))

        # Add contact type filter only if selected
        if self.qa_type_contact:
            domain.append(('show_records_qa', '=', self.qa_type_contact))

        # Add report-specific filter
        if self.print_type == 'by_hand':
            domain.append(('by_hand_qa', '=', True))
            report = self.env.ref('visio_contact_extension_qa.action_report_by_hand_list')
        else:
            report = self.env.ref('visio_contact_extension_qa.action_report_lables_mohsineen')

        # Search and return
        partners = self.env['res.partner'].search(domain)

        if not partners:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "No Records Found",
                    'message': "No partners matched your filters.",
                    'type': 'warning',
                    'sticky': False,
                }
            }

        return report.report_action(partners)

