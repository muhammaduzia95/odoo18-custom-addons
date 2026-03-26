from odoo import models, fields, api

class TTIReportWizard(models.TransientModel):
    _name = 'tti.report.wizard'
    _description = 'TTI Report Wizard'

    report_type = fields.Selection([
        ('party_receivable', 'Party Receivable'),
        ('party_ledger', 'Party Ledger'),
        ('other_2', 'Other Report 2'),
    ], string="Report Type", required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('both', 'Both'),
    ], string="State", required=True , default="posted")

    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        domain="[('employee', '=', False), ('customer_rank', '>', 0) , ('tti_company_category', '=' , 'manufacture')]"
    )

    tax_filter = fields.Selection([
        ('with_tax', 'With Tax'),
        ('without_tax', 'Without Tax'),
    ], string="Tax Filter" , default='with_tax')

    city_zone_ids = fields.Many2many('tti.city.zone', string="City Zones")
    category_ids = fields.Many2many('tti.si.category', string="Categories")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        context_report_type = self.env.context.get('default_report_type')
        if context_report_type:
            res['report_type'] = context_report_type
        return res

    @api.onchange('report_type')
    def _onchange_report_type(self):
        if self.report_type != 'party_receivable':
            self.tax_filter = False
            self.city_zone_ids = False
            self.category_ids = False

    def action_print_report(self):
        self.ensure_one()
        if self.report_type == 'party_receivable':
            return self.env['report.visio_tti_exel_reports.party_receivable_report']._generate_excel(self)
        elif self.report_type == 'party_ledger':
            return self.env['report.visio_tti_exel_reports.party_ledger_report']._generate_excel(self)

    def action_print_pdf_report(self):
        self.ensure_one()
        if self.report_type == 'party_receivable':
            return self.env.ref('visio_tti_exel_reports.party_receivable_pdf_report_action').report_action(
                docids=[self.id])
        elif self.report_type == 'party_ledger':
            return self.env.ref('visio_tti_exel_reports.party_ledger_pdf_report_action').report_action(docids=[self.id])


