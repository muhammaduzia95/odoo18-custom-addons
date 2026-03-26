from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class CRMLine(models.Model):
    _name = 'crm.lead.customer.line'


    partner_id  = fields.Many2one('res.partner', string = 'Bidder')
    lead_id  = fields.Many2one('crm.lead', string = 'Customer')
    scope_of_work = fields.Char(string = 'Scope Of Work', readonly=False, store=True)
    expected_closing_date = fields.Datetime("Expected Closing Date", readonly=False)

    # Quote Reference Fields
    x_studio_aa_quote_ref = fields.Char(
        string='AA Quote Ref.',
        help='AA Quote Reference number'
    )

    x_studio_eme_quote_ref = fields.Char(
        string='EME Quote Ref.',
        help='EME Quote Reference number'
    )

    x_studio_lt_quote_ref = fields.Char(
        string='LT Quote Ref.',
        help='LT Quote Reference number'
    )

    # Boolean Fields for Quotations
    x_studio_boolean_field_6nt_1ikjp945u = fields.Boolean(
        string='EME Quoted',
        help='Indicates if EME has provided a quote'
    )

    x_studio_quoted_from_aa = fields.Boolean(
        string='AA Quoted',
        help='Indicates if AA has provided a quote'
    )

    x_studio_quoted_from_lt = fields.Boolean(
        string='LT Quoted',
        help='Indicates if LT has provided a quote'
    )

    # Document Reception Fields
    x_studio_boq_received = fields.Boolean(
        string='BOQ Received',
        help='Bill of Quantities received'
    )

    x_studio_drawings_received = fields.Boolean(
        string='Drawings Received',
        help='Technical drawings received'
    )

    x_studio_specs_received = fields.Boolean(
        string='Specs Received',
        help='Specifications received'
    )

    # Enquiry Reception Fields
    x_studio_enq_received_by_pl = fields.Boolean(
        string='PL Enq. Received',
        help='Enquiry received by PL department'
    )

    x_studio_enquiry_received_by_aa = fields.Boolean(
        string='AA Enq. Received',
        help='Enquiry received by AA department'
    )

    x_studio_enquiry_received_by_eme = fields.Boolean(
        string='EME Enq. Received',
        help='Enquiry received by EME department'
    )

    x_studio_enquiry_received_by_lt = fields.Boolean(
        string='LT Enq. Received',
        help='Enquiry received by LT department'
    )

    # Design and Process Fields
    x_studio_eme_design = fields.Boolean(
        string='EME Design',
        help='EME design required or completed'
    )

    # Text Fields
    x_studio_char_field_7sf_1in6i39mo = fields.Char(
        string='New Text',
        help='Additional text field 1'
    )

    x_studio_char_field_94p_1ikk2jffl = fields.Char(
        string='New Text',
        help='Additional text field 2'
    )

    x_studio_consultant_text = fields.Char(
        string='Consultant Text',
        help='Consultant additional information'
    )

    x_studio_contractor = fields.Char(
        string='Contractor Text',
        help='Contractor additional information'
    )

    x_studio_eme_folder_location = fields.Char(
        string='EME Folder Location',
        help='EME folder location path'
    )

    x_studio_folder_location = fields.Char(
        string='Folder Location',
        help='General folder location path'
    )

    x_studio_scope_of_work = fields.Char(
        string='Scope of Work',
        help='Description of work scope'
    )

    # Many2one Relationship Fields
    x_studio_consultant = fields.Many2one(
        'res.partner',
        string='Consultant',
        help='Consultant partner',
        domain=[('is_company', '=', True)]
    )

    x_studio_contractor_1 = fields.Many2one(
        'res.partner',
        string='Contractor',
        help='Contractor partner',
        domain=[('is_company', '=', True)]
    )

    x_studio_division_1 = fields.Many2one(
        'x_division',
        string='Division',
        help='Division assignment'
    )

    x_studio_sales_team = fields.Many2one(
        'crm.team',
        string='Sales Team',
        help='Assigned sales team'
    )

    # Date Fields
    x_studio_enq_date = fields.Date(
        string='Enq Date',
        help='Enquiry date'
    )

    @api.onchange('x_studio_consultant')
    def _onchange_consultant(self):
        """Update consultant text when consultant is selected"""
        if self.x_studio_consultant:
            self.x_studio_consultant_text = self.x_studio_consultant.name

    @api.onchange('x_studio_contractor_1')
    def _onchange_contractor(self):
        """Update contractor text when contractor is selected"""
        if self.x_studio_contractor_1:
            self.x_studio_contractor = self.x_studio_contractor_1.name

    @api.model
    def create(self, vals):
        """Set enquiry date to today if not provided"""
        if not vals.get('x_studio_enq_date'):
            vals['x_studio_enq_date'] = fields.Date.today()
        return super(CRMLine, self).create(vals)

