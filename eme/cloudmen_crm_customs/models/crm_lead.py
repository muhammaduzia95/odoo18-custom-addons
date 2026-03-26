from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    partner_id = fields.Many2one('res.partner', string='Customer To invoice', required=False)
    x_studio_contractor = fields.Many2one('res.partner', string='Contractor', required=False)
    x_studio_consultant = fields.Many2one('res.partner', string='Consultant', required=False)
    x_studio_consultant_1 = fields.Many2one('res.partner', string='Consultant 1', required=False)
    lead_customer_ids = fields.One2many('crm.lead.customer.line', 'lead_id', string="Customer", copy=True)
    is_tender_stage = fields.Boolean(string='Active', compute="_compute_is_tender_stage")

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
    # FIXED: Renamed to avoid conflict with Many2one field above
    x_studio_contractor_text = fields.Char(
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

    # Many2one Relationship Fields (removed duplicates)
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

    @api.onchange('x_studio_contractor')
    def _onchange_contractor(self):
        """Update contractor text when contractor is selected"""
        if self.x_studio_contractor:
            self.x_studio_contractor_text = self.x_studio_contractor.name

    @api.model
    def create(self, vals):
        """Set enquiry date to today if not provided"""
        if not vals.get('x_studio_enq_date'):
            vals['x_studio_enq_date'] = fields.Date.today()
        return super(CRMLead, self).create(vals)

    @api.onchange('team_id', 'x_studio_contractor', 'x_studio_consultant')
    def get_client_type(self):
        if self.x_studio_contractor and self.team_id.client_type == 'contractor':
            self.partner_id = self.x_studio_contractor
        elif self.x_studio_consultant and self.team_id.client_type == 'consultant':
            self.partner_id = self.x_studio_consultant
        else:
            self.partner_id = self.x_studio_consultant_1

    def prepare_opportunity_quotation_for_lines(self):
        """ Prepares the context for a new quotation (sale.order) by sharing the values of common fields """
        self.ensure_one()
        quotation_context = {
            'default_opportunity_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)]
        }
        if self.team_id:
            quotation_context['default_team_id'] = self.team_id.id
        if self.user_id:
            quotation_context['default_user_id'] = self.user_id.id
        return quotation_context

    def action_sale_quotations_new(self):
        # Call the parent method first
        ret = super(CRMLead, self).action_sale_quotations_new()

        # Create sale orders for each customer in the lines
        sale_orders = []
        for customer_line in self.lead_customer_ids:
            if customer_line.partner_id:
                # Prepare context for this specific customer
                quotation_context = {
                    'default_opportunity_id': self.id,
                    'default_partner_id': customer_line.partner_id.id,
                    'default_campaign_id': self.campaign_id.id,
                    'default_medium_id': self.medium_id.id,
                    'default_origin': self.name,
                    'default_source_id': self.source_id.id,
                    'default_company_id': self.company_id.id or self.env.company.id,
                    'default_tag_ids': [(6, 0, self.tag_ids.ids)],
                    'default_date_order': customer_line.expected_closing_date or fields.Datetime.now(),
                }

                if self.team_id:
                    quotation_context['default_team_id'] = self.team_id.id
                if self.user_id:
                    quotation_context['default_user_id'] = self.user_id.id

                # Create sale order for this customer
                sale_order = self.env['sale.order'].with_context(quotation_context).create({
                    'partner_id': customer_line.partner_id.id,
                    'opportunity_id': self.id,
                    'campaign_id': self.campaign_id.id,
                    'medium_id': self.medium_id.id,
                    'source_id': self.source_id.id,
                    'team_id': self.team_id.id if self.team_id else False,
                    'user_id': self.user_id.id if self.user_id else False,
                    'origin': self.name,
                    'company_id': self.company_id.id or self.env.company.id,
                    'tag_ids': [(6, 0, self.tag_ids.ids)],
                    'date_order': customer_line.expected_closing_date or fields.Datetime.now(),
                    'note': customer_line.scope_of_work or '',
                })
                sale_orders.append(sale_order.id)

        # If sale orders were created, modify the return action to show them
        if sale_orders:
            if len(sale_orders) == 1:
                # If only one sale order, open it directly
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Quotation'),
                    'res_model': 'sale.order',
                    'res_id': sale_orders[0],
                    'view_mode': 'form',
                    'context': {'default_opportunity_id': self.id}
                }
            else:
                # If multiple sale orders, show them in a list
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Quotations'),
                    'res_model': 'sale.order',
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', sale_orders)],
                    'context': {'default_opportunity_id': self.id}
                }

        return ret

    @api.depends('stage_id')
    def _compute_is_tender_stage(self):
        for opportunity in self:
            if hasattr(opportunity.stage_id, 'is_tender_stage') and opportunity.stage_id.is_tender_stage:
                opportunity.is_tender_stage = True
            else:
                opportunity.is_tender_stage = False