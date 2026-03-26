from odoo import models, fields, api, Command
from odoo.osv import expression
from zeep.xsd import default_types


# class PurposeOfVisit(models.Model):
#     _name = 'tti.crm.purpose.visit'
#     _description = 'Purpose of Visit'
#
#     name = fields.Char(string='Purpose', required=True)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    tti_lead_id = fields.Char(string='Tti Lead ID')
    tti_start_time = fields.Datetime(string='Start Time')
    tti_completion_time = fields.Datetime(string='Completion Time')
    tti_last_modified_time = fields.Datetime(string='Last Modified Time')

    tti_salesperson_email = fields.Char(string='Salesperson Email')
    tti_salesperson_name = fields.Char(string='Salesperson Name')

    # Section 1: Testing & Visit Details
    tti_purpose_of_visit = fields.Selection([
            ('sales_pitch', 'Sales Pitch'),
            ('follow_up_visit', 'Follow Up Visit'),
            ('sample_collection', 'Sample Collection'),
            ('complaint_handling', 'Complaint Handling'),
        ], string='Purpose of Visit'
    )
    tti_client_type = fields.Selection([
            ('new', 'New'),
            ('existing', 'Existing'),
        ],
        string='Client Type',
        default='existing',
        compute="_tti_client_type", store=True,
    )
    bg_color = fields.Char(string="Background Color", compute="_compute_background_color")

    @api.depends('tti_client_type', 'tti_purpose_of_visit')
    def _compute_background_color(self):
        for record in self:
            if record.tti_client_type == "new" and record.tti_purpose_of_visit == "sales_pitch":
                record.bg_color = "#8fd19e"
            else:
                record.bg_color = "#FFFFFF"

    @api.depends('tti_purpose_of_visit')
    def _tti_client_type(self):
        for record in self:
            if record.tti_purpose_of_visit == 'sales_pitch':
                record.tti_client_type = 'new'
            else:
                record.tti_client_type = 'existing'


    # Section 2: For New Clients and Existing Clients based on client_type
    tti_client_name = fields.Char(string='Client Name')
    tti_testing_category = fields.Char(string='Testing Category')
    tti_visit_details = fields.Text(string='Visit Details')

    # Section 2: For New Clients
    tti_client_address = fields.Char(string='Client Address')
    tti_contact_person_name = fields.Char(string='Contact Person')
    tti_contact_person_phone = fields.Char(string='Contact Phone')
    tti_contact_person_email = fields.Char(string='Contact Email')

    def write(self, vals):
        res = super(CRMLead, self).write(vals)
        print(vals)
        if vals.get('tti_purpose_of_visit') and vals.get('tti_purpose_of_visit') == 'sales_pitch':
            self.partner_id = False
            self.description = False
        return res