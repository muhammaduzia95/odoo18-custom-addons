from email.policy import default
import os

from odoo import models, fields, api, Command, _
import logging
import string
import base64
import requests
import traceback
import json
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, timedelta
from odoo.tools import image as image_tools

_logger = logging.getLogger(__name__)


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    partner_category_ids = fields.Many2many('res.partner.category', related='partner_id.category_id', readonly=True)


class SaleReport(models.Model):
    _inherit = 'sale.report'

    partner_category_ids = fields.Many2many('res.partner.category', related='partner_id.category_id', readonly=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_zone = fields.Char(compute='_compute_partner_address', string='Zone', store=False)
    partner_zone_id = fields.Many2one(related='partner_id.tti_city_zone_id', string='Zone', store=True, readonly=False)
    partner_street = fields.Char(compute='_compute_partner_address', string='Street', store=False)
    partner_street2 = fields.Char(compute='_compute_partner_address', string='Street 2', readonly=True, store=False)
    partner_city = fields.Char(compute='_compute_partner_address', string='City', readonly=True, store=False)
    partner_state_id = fields.Many2one('res.country.state', compute='_compute_partner_address', string='State',
                                       readonly=True, store=False)
    partner_zip = fields.Char(compute='_compute_partner_address', string='Zip', readonly=True, store=False)
    partner_country_id = fields.Many2one('res.country', compute='_compute_partner_address', string='Country',
                                         readonly=True, store=False)

    total_pkr = fields.Float(string="Total PKR" , compute="_compute_total_pkr" , store=True)

    @api.depends('amount_total', 'pricelist_id', 'date_order')
    def _compute_total_pkr(self):
        for order in self:
            currency = order.pricelist_id.currency_id
            order.total_pkr = 0.0

            if currency.name == 'PKR':
                order.total_pkr = order.amount_total
                continue

            if order.amount_total and order.date_order:
                pkr = self.env['res.currency'].search([('name','=','PKR')])
                rate = currency._get_conversion_rate(
                    from_currency=currency,
                    to_currency=pkr,
                    company=order.company_id,
                    date=order.date_order
                )
                order.total_pkr = order.amount_total * rate
            else:
                order.total_pkr = 0.0

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Salesperson",
        compute='_compute_user_id',
        store=True, readonly=False, precompute=True, index=True,
        tracking=2,
        copy=False,
        domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ))

    # @api.onchange('pricelist_id')
    # def update_currency(self):
    #     for record in self:
    #         if record.pricelist_id and record.pricelist_id.currency_id:
    #             record.tti_currency_from = record.pricelist_id.currency_id

    @api.depends('partner_id')
    def _compute_partner_address(self):
        for order in self:
            order.partner_zone = order.partner_id.tti_city_zone_id.name if order.partner_id.tti_city_zone_id else ''
            order.partner_street = order.partner_id.street
            order.partner_street2 = order.partner_id.street2
            order.partner_city = order.partner_id.city
            order.partner_state_id = order.partner_id.state_id
            order.partner_zip = order.partner_id.zip
            order.partner_country_id = order.partner_id.country_id

    # barcode = fields.Char(string='Barcode', default=lambda self: self._get_random_barcode(), readonly=True, copy=False)
    #
    # @api.model
    # def _get_random_barcode(self):
    #     return str(int.from_bytes(os.urandom(8), 'little'))

    tti_care_label_image_three_six = fields.Char(string="Care Label 6 Image Name OLD Removed", copy=False)

    credit = fields.Monetary(string="Total Receivable", related='partner_id.credit')

    total_receivable = fields.Monetary(
        string='Total Receivable Amount',
        compute='_compute_total_receivable',
        store=True,
        currency_field='currency_id',
    )

    @api.depends('partner_id')
    def _compute_total_receivable(self):
        for order in self:
            if order.partner_id:
                invoices = self.env['account.move'].search([
                    ('partner_id', '=', order.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                ])
                order.total_receivable = sum(invoices.mapped('amount_residual'))
            else:
                order.total_receivable = 0.0

    def _default_tti_branch(self):
        branch = self.env['res.partner'].search([
            ('tti_company_category', '=', 'branch'),
            ('name', '=', 'Lahore Main Branch'),
        ], limit=1)
        return branch.id if branch else False

    tti_branch = fields.Many2one('res.partner', domain=[('tti_company_category', '=', 'branch')], string='Branch',
                                 default=lambda self: self._default_tti_branch())
    state = fields.Selection(
        selection_add=[('sent_to_lims', 'Sent to LIMS'), ('approved', 'Approved'), ('quotation_done', 'Quotation Done'),
                       ('update_sale_order', 'Update Sale Order'), ('quotation_approved', 'Quotation Approved')],
        ondelete={'sent_to_lims': 'set default', 'approved': 'set default'})
    tti_lims_api_response = fields.Text(string="LIMS API Response", copy=False)
    tti_lims_api_response_check = fields.Boolean(string="LIMS API Response Check", copy=False)
    hide_lock_btns = fields.Boolean(string="Hide lock button", default=False, compute="compute_hide_lock_buttons")

    @api.depends('invoice_ids', 'invoice_ids.state')
    def compute_hide_lock_buttons(self):
        for order in self:
            if order.invoice_ids and order.invoice_ids.filtered(lambda inv: inv.state != "cancel"):
                order.hide_lock_btns = True
            else:
                order.hide_lock_btns = False

    sale_email_ids = fields.One2many(
        'sale.emails', 'sale_order_id', string="Emails", copy=True
    )

    user_has_group_tti_enable_so_price = fields.Boolean(
        compute="_compute_user_has_group_tti_enable_so_price",
        default=False
    )

    user_has_group_tti_allow_taxes = fields.Boolean(
        compute="_compute_user_has_group_tti_allow_taxes",
        default=False
    )

    def _compute_user_has_group_tti_allow_taxes(self):
        has_group = self.env.user.has_group('visio_tti_so_customize.group_tti_allow_taxes')
        for record in self:
            record.user_has_group_tti_allow_taxes = has_group

    commitment_date = fields.Datetime(
        default=lambda self: fields.Datetime.now() + timedelta(hours=48)
    )

    @api.onchange('date_order')
    def _onchange_date_order_commitment(self):
        """Set default commitment_date 48 hours after date_order on change"""
        # print("Email Line IDs:", self.sale_email_ids.ids)
        if self.date_order:
            self.commitment_date = self.date_order + timedelta(hours=48)

    @api.constrains('date_order', 'commitment_date')
    def _check_commitment_date(self):
        for order in self:
            if order.commitment_date and order.date_order:
                if order.commitment_date < order.date_order:
                    raise ValidationError("Delivery Date must be after Order Date.")

    def _compute_user_has_group_tti_enable_so_price(self):
        has_group = self.env.user.has_group('visio_tti_so_customize.group_tti_enable_so_price')
        for record in self:
            record.user_has_group_tti_enable_so_price = has_group

    def action_quotation_done(self):
        self.ensure_one()
        self.state = 'quotation_done'
        for record in self:
            if record.tti_pi_applicant:
                if not record.tti_pi_applicant.phone or not record.tti_pi_applicant.email or not record.tti_pi_applicant.function:
                    raise ValidationError("Please make sure applicant has Phone , Job position and Email.")

    def action_quotation_approved(self):
        self.ensure_one()
        self.state = 'quotation_approved'
        for record in self:
            if record.tti_si_select_partner == 'tti_testing':
                record.sale_order_no = self.env['ir.sequence'].next_by_code('sale.order.sequence')
            elif record.tti_si_select_partner == 'mts':
                record.sale_order_no = self.env['ir.sequence'].next_by_code('mts.sale.order')
            record.name = record.sale_order_no

    sale_order_no = fields.Char(string="Sale Order No", readonly=True, copy=False)
    quotation_num = fields.Char(string="Quotation No", readonly=True, copy=False)

    # @api.depends('name')
    # def _compute_quotation_no(self):
    #     for record in self:
    #         if record.state == 'draft':
    #             record.quotation_num = record.name
    #         else:
    #             record.quotation_num = ''

    report_urls_html = fields.Html(string="Report URLs", copy=False)

    @api.onchange('partner_id', 'order_line')
    def _onchange_partner_id_apply_taxes(self):
        """Apply sales_taxes from res.partner to all order lines when partner_id is changed."""
        for order in self:
            if order.partner_id:
                for line in order.order_line:
                    line.tax_id = [(6, 0, (line.tax_id.ids + order.partner_id.sales_taxes.ids))]

    def action_confirm(self):
        res = super().action_confirm()
        # if not self.tti_lims_api_response_check:
        #     raise ValidationError("Please approve the sale order first.")
        if not self.partner_id.vat or not self.partner_id.street or not self.partner_id.state_id or not self.partner_id.tti_city_zone_id:
            raise ValidationError("Please make sure manufacturer has NTN , Address , State and Zone.")
        if not self.tti_parcel_id:
            raise ValidationError("Please add Parcels.")
        try:
            self.action_sale_order_sent_to_lims()
        except Exception as e:
            raise ValidationError(f"Error confirming Sale Order: {str(e)}")
        return res

    def action_approved_now(self):
        self.ensure_one()
        self.state = 'approved'
        # self.action_confirm()

    def action_cancel(self):
        if not self.env.user.has_group('visio_tti_so_customize.group_tti_so_allow_cancel_so'):
            raise ValidationError(
                "You have no access to cancel this sale order. Please, contact with administrator !!!")
        res = super().action_cancel()
        if self.tti_lims_api_response_check:
            self.action_sale_order_sent_to_lims(cancel_on_lims=True)
        return res

    def action_confirm_now(self):
        self.ensure_one()
        print(self.state)
        # if not self.tti_lims_api_response_check:
        #     raise ValidationError("Please approve the sale order first.")
        self.state = 'draft'
        self.action_confirm()

    def action_attach_report(self):
        """Fetch reports and attach them to the sale order"""
        self.ensure_one()
        tests_report_url = f"http://202.59.76.150/api/reportlink/{self.name}"
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.get(tests_report_url, headers=headers, timeout=30)
            response_data = response.json()

            if response.status_code == 200 and isinstance(response_data, list):
                self.tti_lims_api_response += '\n\n' + str(json.dumps(response_data, indent=4))

                # Start HTML table
                html_table = """
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Reports</th>
                            <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Requisitions</th>
                            <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Barcodes</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                for test in response_data:
                    try:
                        report_url = test.get("reporturl")
                        requisition_url = test.get("viewrequisition")
                        barcode_url = test.get("barcodeprint")
                        test_name = test.get("testname", "Report")
                        test_code = test.get("testcode")

                        html_table += f"""
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">
                        """

                        # Report button (first column)
                        if report_url:
                            report_response = requests.get(report_url, timeout=30)
                            if report_response.status_code == 200:
                                # file_content = base64.b64encode(report_response.content)
                                # file_name = f"{test_name}.pdf"

                                # attachment_vals = {
                                #     "name": file_name,
                                #     "datas": file_content,
                                #     "res_model": "sale.order",
                                #     "res_id": self.id,
                                #     "mimetype": "application/pdf",
                                # }
                                # attachment = self.env["ir.attachment"].create(attachment_vals)

                                html_table += f"""
                                <a href="{report_url}" style="
                                    display: inline-block;
                                    padding: 6px 10px;
                                    margin: 3px 0;
                                    background-color: #6c757d;
                                    color: #fff;
                                    text-align: left;
                                    border: none;
                                    border-radius: 4px;
                                    text-decoration: none;
                                    font-size: 12px;
                                ">
                                    [{test_code or ""}] {test_name}
                                </a>
                                """
                            else:
                                _logger.error(
                                    f"Failed to download report from {report_url}, HTTP Status: {report_response.status_code}")

                        # Close first column, open second column
                        html_table += """
                            </td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">
                        """

                        # Requisition button (second column)
                        if requisition_url:
                            html_table += f"""
                            <a href="{requisition_url}" target="_blank" style="
                                display: inline-block;
                                padding: 6px 10px;
                                margin: 3px 0;
                                background-color: #17a2b8;
                                color: #fff;
                                text-align: left;
                                border: none;
                                border-radius: 4px;
                                text-decoration: none;
                                font-size: 12px;
                            ">
                                [{test_code or ""}] {test_name} 
                            </a>
                            """

                        # Close second column, open third column
                        html_table += """
                            </td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">
                        """

                        # Barcode button (third column)
                        if barcode_url:
                            html_table += f"""
                            <a href="{barcode_url}" target="_blank" style="
                                display: inline-block;
                                padding: 6px 10px;
                                margin: 3px 0;
                                background-color: #28a745;
                                color: #fff;
                                text-align: left;
                                border: none;
                                border-radius: 4px;
                                text-decoration: none;
                                font-size: 12px;
                            ">
                                [{test_code or ""}] {test_name} 
                            </a>
                            """

                        # Close row
                        html_table += """
                            </td>
                        </tr>
                        """

                    except Exception as e:
                        _logger.error(f"Error processing test {test.get('testname')}: {str(e)}")
                        continue

                # Close table
                html_table += """
                    </tbody>
                </table>
                """

                self.report_urls_html = html_table

            else:
                raise UserError("Invalid API response format")

        except Exception as e:
            error_message = f"Error fetching reports: {str(e)}"
            _logger.error(error_message)
            raise UserError(error_message)

    def get_test_details(self, cancel_on_lims=False):
        result = {}
        for order in self:
            test_details = []
            lines = order.order_line.filtered(
                lambda x: x.test_type in ['test_package', 'test_report'] and x.product_id and x.default_code)
            if len(lines) <= 0:
                raise UserError("Test or Packages Not Found for send to lims, please try again")
            package_lines = lines.filtered(lambda x: x.test_type == 'test_package')
            test_lines = lines.filtered(lambda x: x.test_type == 'test_report')

            if cancel_on_lims:
                for package_line in package_lines:
                    package_test_lines = order.tti_test_report_line_ids.filtered(
                        lambda x: x.package_id.id == package_line.product_template_id.id)
                    package_test_lines_details = [{
                        "odoorecordno": package_test_line.new_unique_number if package_test_line.new_unique_number else package_test_line.id or 0,
                        "testcode": package_test_line.default_code or 0,
                        "packageqty": 0,
                        "packagename": package_line.product_template_id.name or "",
                        "composits": package_test_line.composites or "",
                        "packagecode": package_line.default_code or 0,
                        "qty": 0,
                        "comments": package_test_line.comments or "",
                        "status": "1" if package_test_line.qty <= 0 or package_line.product_uom_qty <= 0 else "0",
                    } for package_test_line in package_test_lines]
                    # print('package_test_lines_details = ', package_test_lines_details)
                    test_details += package_test_lines_details

                test_lines_details = [{
                    "odoorecordno": test_line.new_unique_number if test_line.new_unique_number else test_line.id or 0,
                    "testcode": test_line.default_code or 0,
                    "packageqty": 0,
                    "packagename": "",
                    "composits": test_line.composites or "",
                    "packagecode": 0,
                    "qty": 0,
                    "comments": test_line.comments or "",
                    "status": "1" if test_line.product_uom_qty <= 0 else "0",
                } for test_line in test_lines]
                # print('test_lines_details = ', test_lines_details)
                test_details += test_lines_details

            else:
                for package_line in package_lines:
                    package_test_lines = order.tti_test_report_line_ids.filtered(
                        lambda x: x.package_id.id == package_line.product_template_id.id)
                    package_test_lines_details = [{
                        "odoorecordno": package_test_line.new_unique_number if package_test_line.new_unique_number else package_test_line.id or 0,
                        "testcode": package_test_line.default_code or 0,
                        "packageqty": int(package_line.product_uom_qty) or 0,
                        "packagename": package_line.product_template_id.name or "",
                        "composits": package_test_line.composites or "",
                        "packagecode": package_line.default_code or 0,
                        "qty": int(package_test_line.qty) or 0,
                        "comments": package_test_line.comments or "",
                        "status": "1" if package_test_line.qty <= 0 or package_line.product_uom_qty <= 0 else "0",
                    } for package_test_line in package_test_lines]
                    # print('package_test_lines_details = ', package_test_lines_details)
                    test_details += package_test_lines_details

                test_lines_details = [{
                    "odoorecordno": test_line.new_unique_number if test_line.new_unique_number else test_line.id or 0,
                    "testcode": test_line.default_code or 0,
                    "packageqty": 0,
                    "packagename": "",
                    "composits": test_line.composites or "",
                    "packagecode": 0,
                    "qty": int(test_line.product_uom_qty) or 0,
                    "comments": test_line.comments or "",
                    "status": "1" if test_line.product_uom_qty <= 0 else "0",
                } for test_line in test_lines]
                # print('test_lines_details = ', test_lines_details)
                test_details += test_lines_details

            result[order.id] = test_details
        return result

    def action_update_sale_order(self):
        self.ensure_one()
        self.action_sale_order_sent_to_lims()
        # self.state = 'update_sale_order'

    def _to_user_tz(self, datetime):
        """Convert UTC datetime to the user's timezone."""
        user_tz = fields.Datetime.context_timestamp(self.env.user, datetime)
        return user_tz.strftime("%d/%m/%Y %H:%M:%S")

    def action_sale_order_sent_to_lims(self, validation_check=True, cancel_on_lims=False):
        """Send Sale Order details to the external API."""
        self.ensure_one()
        record = self

        def get_attachment_url(attachment):
            if not attachment.public:
                attachment.sudo().write({
                    'public': True
                })
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            return f"{base_url}/web/content/{attachment.id}" if attachment else ""

        url = "http://202.59.76.150/api/newsaleorder"
        headers = {
            "Content-Type": "application/json",
        }

        tti_so_component_breakdown_ids = reversed(record.tti_so_component_breakdown_ids)
        test_details = record.get_test_details(cancel_on_lims=cancel_on_lims).get(record.id, [])

        # if record.tti_pi_buyer and record.tti_pi_buyer.tti_is_photo_lims:
        #     if record.tti_pi_buyer.image_1920 and not record.tti_pi_buyer.tti_lims_logo_report:
        #         record.tti_pi_buyer._create_image_attachment(record.tti_pi_buyer.image_1920)

        payload = {
            # "newimage": "\\AppServer\\samplepic\\Kik Test Requisition Form - P255539.docx",
            "newimage": "https://images.pexels.com/photos/259915/pexels-photo-259915.jpeg",
            "newemails": "asifiqbal@abdulwahidoomer.com",
            "revisedreportno": record.tti_si_p_report or "",

            # Client/Sample Info

            # Header info
            "useremail": record.user_id.email or "",
            "branchcode": record.tti_branch.code if record.tti_branch else "",
            "reportdate": self._to_user_tz(record.commitment_date) if record.commitment_date else "",
            # TODO: Format "28/02/2025 16:59:00",
            "dateregistration": self._to_user_tz(record.date_order) if record.date_order else "",
            # TODO: Format "28/02/2025 16:59:00",

            "reportno": record.name,
            "referenceno": f"{record.id}",
            "sampledate": self._to_user_tz(record.create_date) if record.date_order else "",
            # TODO: Format "28/02/2025 16:59:00"

            # Party Information
            "manufacturername": record.partner_id.name or "",
            "manufacturercode": record.partner_id.code or "",
            "applicant": record.tti_pi_applicant.name or "",
            "cc": record.tti_pi_email_cc or "",

            "reportLogoUrl": f"{get_attachment_url(record.tti_pi_buyer.tti_lims_logo_report)}/{record.tti_pi_buyer.tti_lims_logo_report_name}" if record.tti_pi_buyer and record.tti_pi_buyer.tti_is_photo_lims and record.tti_pi_buyer.tti_lims_logo_report and record.tti_pi_buyer.tti_lims_logo_report_name else "",
            "kikReport": "Y" if record.tti_pi_buyer and record.tti_pi_buyer.tti_is_kik_report else "N",

            "reporttoname": record.partner_id.name or "",
            "faxno": record.partner_id.phone or record.partner_id.mobile or '' if record.partner_id else "",
            "address1": f"{record.partner_id.street or ''} {record.partner_id.street2 or ''}" if record.partner_id else "",
            "emailid": record.tti_pi_applicant.email if record.tti_pi_applicant and record.tti_pi_applicant.email else "",
            "contactno": record.tti_pi_applicant.mobile or record.tti_pi_applicant.phone or '' if record.tti_pi_applicant else "",

            "buyername": record.tti_pi_buyer.name or "",
            "buyercode": record.tti_pi_buyer.code or "",
            "subbrandname": record.tti_pi_brand_id.name or "",
            "agentcode": record.tti_pi_agent_id.code or "",
            "agentname": record.tti_pi_agent_id.name or "",

            # Sample Information
            "samplecategorycode": record.tti_si_category.code or "",
            "samplecategoryname": record.tti_si_category.name or "",
            # "productcategoryname": record.tti_si_product_category.name or "",
            "productcategoryname": record.tti_si_product_category_text or "",
            "subcategoryname": record.tti_si_sub_category.name or "",
            "producttypename": record.tti_si_product_type.name or "",

            "programname": record.tti_si_program.name or "",
            "originname": record.tti_si_origin.name or "",
            "destinationname": record.tti_si_destination.name or "",

            "season": record.tti_si_season or "",
            "po": record.tti_si_po or "",
            "spinstruction": record.tti_si_sp_inst or "",
            "sampledesc": record.tti_si_description or "",
            "careinst": record.tti_si_care_inst or "",
            "fabric": record.tti_si_fabric or "",
            "styleno": record.tti_si_style_no or "",
            "colour": record.tti_si_colour or "",
            "sampleweight": str(record.tti_si_weight) or "",

            "testno": record.tti_si_test_no or "",

            "enduse": record.tti_si_end_use or "",
            "construction": record.tti_si_construction or "",
            "department": record.tti_si_dept or "",
            "stylename": record.tti_si_style or "",
            "size": record.tti_si_size or "",

            # ===============================NEW UPDATED KEY and VALUES===============================================
            "fiberlbl": "fiber",
            "fibername": record.tti_fiber_si or "",

            "designlbl": "design",
            "design": record.tti_si_design or "",

            "dyestufflbl": "dye stuff",
            "dyestuffname": record.tti_si_dye_stuff.name or "",

            "protocollbl": "protocol",
            "protocol": record.tti_si_protocol or "",

            "umolbl": "weight",
            "unit": record.tti_si_uom.name or "",

            "vrnolbl": "v.r.n",
            "vrno": record.tti_si_vr_no or "",

            # "preportlbl": "",
            # "orderqtylbl": "",
            # "articlenamelbl": "article",
            # =======================================================================================================

            "label1": record.tti_si_label_1_name or "",
            "label2": record.tti_si_label_2_name or "",
            "label3": record.tti_si_label_3_name or "",
            "label4": record.tti_si_label_4_name or "",
            "input1": record.tti_si_label_1_value or "",
            "input2": record.tti_si_label_2_value or "",
            "input3": record.tti_si_label_3_value or "",
            "input4": record.tti_si_label_4_value or "",

            "email1": record.tti_ci_email1 or "",
            "email2": record.tti_ci_email2 or "",
            "email3": record.tti_ci_email3 or "",
            "email4": record.tti_ci_email4 or "",
            "email5": record.tti_ci_email5 or "",

            # Tests and Packages Details
            "testdetail": test_details,

            # Image Upload
            "imagesdetail": [{
                "imagepath": f"{get_attachment_url(attachment_id)}/{attachment_id.name}",
                "imagename": attachment_id.name,
            } for attachment_id in record.tti_attachment_ids],

            # Care Label Images Upload
            "careimage1": f"{get_attachment_url(record.tti_care_label_image_one_id)}/{record.tti_care_label_image_one_name}" if record.tti_care_label_image_one_name and record.tti_care_label_image_one_id else "",
            "careimage2": f"{get_attachment_url(record.tti_care_label_image_two_id)}/{record.tti_care_label_image_two_name}" if record.tti_care_label_image_two_name and record.tti_care_label_image_two_id else "",
            "careimage3": f"{get_attachment_url(record.tti_care_label_image_three_id)}/{record.tti_care_label_image_three_name}" if record.tti_care_label_image_three_name and record.tti_care_label_image_three_id else "",
            "careimage4": f"{get_attachment_url(record.tti_care_label_image_four_id)}/{record.tti_care_label_image_four_name}" if record.tti_care_label_image_four_name and record.tti_care_label_image_four_id else "",
            "careimage5": f"{get_attachment_url(record.tti_care_label_image_five_id)}/{record.tti_care_label_image_five_name}" if record.tti_care_label_image_five_name and record.tti_care_label_image_five_id else "",
            "careimage6": f"{get_attachment_url(record.tti_care_label_image_six_id)}/{record.tti_care_label_image_six_name}" if record.tti_care_label_image_six_name and record.tti_care_label_image_six_id else "",

            # Component Breakdown
            "oekoimage": f"{get_attachment_url(record.tti_okeo_image_id)}/{record.tti_okeo_image_name}" if record.tti_okeo_image_id and record.tti_okeo_image_name else "",
            "componentimage": f"{get_attachment_url(record.tti_image_comp_breakdown_id)}/{record.tti_image_comp_breakdown_name}" if record.tti_image_comp_breakdown_id and record.tti_image_comp_breakdown_name else "",
            "oekoremarks": record.tti_remarks or "",
            "componentdetail": [
                {
                    "remarks": comp.tti_remarks or "",
                    "sample": comp.tti_sample or "",
                    "materialno": comp.tti_material_no or "",
                    "componentdesc": comp.tti_component_description or "",
                    "materialtype": comp.tti_material_type or "",
                }
                for comp in tti_so_component_breakdown_ids
            ],
        }

        if record.tti_pi_report_to_manufacturer:
            payload.update(
                {
                    "reporttoname": record.tti_pi_report_to_manufacturer.name or "",
                    "faxno": record.tti_pi_report_to_manufacturer.mobile or "",
                    "address1": f"{record.tti_pi_report_to_manufacturer.street or ''} {record.tti_pi_report_to_manufacturer.street2 or ''}" or "",
                    "emailid": record.tti_pi_report_to_manufacturer.email or "",
                    "contactno": record.tti_pi_report_to_manufacturer.phone or "",
                }
            )

        print("payload", payload)

        _logger.info(f"\npayload = {payload}\n")

        # for key, value in payload.items():
        #     print("------ {} = {}".format(key, value))

        try:
            print('record.state = ', record.state)
            if record.state in ['cancel', 'sale'] and record.tti_lims_api_response_check:
                print("updating")
                url = "http://202.59.76.150/api/updatesaleorder"
                response = requests.patch(url, headers=headers, data=json.dumps(payload), timeout=30)
            else:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)

            response_data = response.json()
            print("response data", response_data)
            _logger.info(f"\response = {response}\n")

            if response.status_code == 200:
                _logger.info('API Info --------')
                # ➕ Extract report URLs and build HTML content
                # new_links = ""
                # for item in response_data:
                #     report_url = item.get('reporturl')
                #     test_name = item.get('testname')
                #     if report_url:
                #         new_links += f'<a href="{report_url}" target="_blank">{test_name or "View Report"}</a><br/>\n'
                #
                # # ➕ Append to existing HTML content
                # if new_links:
                #     existing_html = record.report_urls_html or ""
                #     record.report_urls_html = existing_html + new_links

                # Store API response in JSON field
                if isinstance(response_data, list):
                    if validation_check:
                        if response_data[0].get('responsestatus'):  # Assuming 'True' means success
                        # if response_data:  # Assuming 'True' means success
                            if record.state == 'sale' and record.tti_lims_api_response_check:
                                record.message_post(body="API request successful. LIMS Sale Order Updated. Response: %s" % response_data)
                            else:
                                record.message_post(body="API request successful. Response: %s" % response_data)
                                record.write({
                                    # 'state': 'sent_to_lims',
                                    'tti_lims_api_response_check': True,
                                })
                        else:
                            record.message_post(body="API request failed. Response: %s" % response_data)
                            raise UserError("API request failed. Response: %s" % response_data)
                    else:
                        if response_data:  # Assuming 'True' means success
                            if record.state == 'sale' and record.tti_lims_api_response_check:
                                record.message_post(body="API request successful. LIMS Sale Order Updated. Response: %s" % response_data)
                            else:
                                record.message_post(body="API request successful. Response: %s" % response_data)
                                record.write({
                                    # 'state': 'sent_to_lims',
                                    'tti_lims_api_response_check': True,
                                })
                        else:
                            record.message_post(body="API request failed. Response: %s" % response_data)
                            raise UserError("API request failed. Response: %s" % response_data)
                else:
                    record.message_post(body="API request failed. Response: %s" % response_data)
            else:
                record.message_post(
                    body="API request failed. Status Code: %s, Response: %s" % (response.status_code, response_data))
                raise ValidationError(f"API request failed. Response: {response_data}")

            # response_str = record.tti_lims_api_response or ''
            response_str = f'\nPayload : \n{str(json.dumps(payload, indent=4))}\n'
            if isinstance(response_data, list):
                response_str += '\n'.join(
                    f'{str(key).ljust(30)} \t{value},'  # Adjust padding dynamically
                    for data in response_data if isinstance(data, dict)
                    for key, value in data.items()
                ) + '\n'
            else:
                response_str += str(response_data) + '\n'

            response_str += '_' * 150 + '\n\n'  # Ensures a clean separator
            # record.tti_lims_api_response += response_str + '\n'
            record.write({'tti_lims_api_response': response_str})
        except Exception as e:
            values = dict(exception="Error sending API request: %s" % str(e), traceback=traceback.format_exc())
            _logger.error(values)
            raise UserError(f"Error :: {values}")
        return True

    # def action_sale_order_sent_to_lims(self):
    #     """Send Sale Order details to the external API."""
    #     self.ensure_one()
    #     record  = self
    #
    #     url = "http://202.59.76.150/api/newsaleorder"
    #     headers = {
    #         "Content-Type": "application/json",
    #     }
    #
    #     payload = {
    #         "reportno": record.name,
    #         "referenceno": f"{record.id}",
    #         "sampledate": "28/02/2025 16:59:00",
    #         "manufacturername": "KiK Textilien and Non-Food GmbH",
    #         "manufacturercode": 13770,
    #         "newimage": "\\AppServer\\samplepic\\Kik Test Requisition Form - P255539.docx",
    #         "newemails": "asifiqbal@abdulwahidoomer.com",
    #         "oekoimage": "",
    #         "oekoremarks": "test remarks for oek image",
    #         "componentimage": "\\AppServer\\samplepic\\02845-25 Component Pic.JPG",
    #         "label1": "Supplier",
    #         "label2": "Supplier No.",
    #         "label3": "DOB",
    #         "label4": "",
    #         "input1": "Abdul Wahid Omer & Co.",
    #         "input2": "272058",
    #         "input3": "DOB NG",
    #         "input4": "933",
    #         "revisedreportno": "",
    #         "design": "4500456426, 4500456427, 4500456428",
    #         "emailid": "N/A",
    #         "careinst": "",
    #         "fabric": "Fleece",
    #         "styleno": "1201617905, 1201617906",
    #         "colour": "Khaki",
    #         "sampleweight": "280",
    #         "spinstruction": "***No. of sample 9***",
    #         "sampledesc": "W, RN Sweatshirt, cropped, khaki",
    #         "applicant": "Ms. Jessica Buscher",
    #         "cc": "Mr. Asif Iqbal",
    #         "season": "225",
    #         "dateregistration": "28/02/2025 16:59:00",
    #         "buyername": "KIK",
    #         "buyercode": "769",
    #         "unit": "GSM",
    #         "po": "P255539",
    #         "agentcode": 753,
    #         "agentname": "Synergies Sourcing Pakistan",
    #         "samplecategorycode": 6,
    #         "reportdate": "03/03/2025 15:00:00.000",
    #         "useremail": "jamal.khan@ttilabs.net",
    #         "branchcode": -1,
    #         "careimage1": "\\AppServer\\samplepic\\30 Wash normal cycle.jpg",
    #         "careimage2": "\\AppServer\\samplepic\\Do Not Bleach...jpg",
    #         "careimage3": "\\AppServer\\samplepic\\Do Not Tumble Dry.jpg",
    #         "careimage4": "\\AppServer\\samplepic\\Cool Iron (Max. 110).jpg",
    #         "careimage5": "\\AppServer\\samplepic\\Do Not Dry Clean.jpg",
    #         "componentdetail": [
    #             {"remarks": "", "sample": "A", "materialno": "A1", "componentdesc": "Body Fabric (Black)",
    #              "materialtype": "Substrate"},
    #             {"remarks": "", "sample": "A", "materialno": "A2", "componentdesc": "Chest Print (Camel)",
    #              "materialtype": "Surface Coating"},
    #             {"remarks": "", "sample": "A", "materialno": "A3", "componentdesc": "Chest Print (Beige)",
    #              "materialtype": "Surface Coating"},
    #             {"remarks": "", "sample": "A", "materialno": "A4", "componentdesc": "Rib Fabric (Black)",
    #              "materialtype": "Substrate"},
    #         ],
    #         "testdetail": [
    #             {"testcode": 5789, "packageqty": 1, "packagename": "C1 (Basic)", "composits": "A1", "packagecode": 4988,
    #              "qty": 2, "comments": "", "status": "0"},
    #             {"testcode": 1956, "packageqty": 1, "packagename": "C1 (Basic)", "composits": "", "packagecode": 4988,
    #              "qty": 1, "comments": "Not Required", "status": "0"},
    #         ],
    #         "imagesdetail": [{"imagepath": "", "imagename": ""}]
    #     }
    #
    #     try:
    #         response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    #         response_data = response.json()
    #
    #         if response.status_code == 200:
    #             _logger.info('API Info --------')
    #             # Store API response in JSON field
    #
    #             if response_data[0].get('responsestatus'):  # Assuming 'True' means success
    #                 record.message_post(body="API request successful. Response: %s" % response_data)
    #                 record.write({'state': 'sent_to_lims'})
    #             else:
    #                 record.message_post(body="API request failed. Response: %s" % response_data)
    #                 # raise UserError("API request failed. Response: %s" % response_data)
    #         else:
    #             record.message_post(body="API request failed. Status Code: %s, Response: %s" % (response.status_code, response_data))
    #             # raise UserError("API request failed. Status Code: %s, Response: %s" % (response.status_code, response_data))
    #
    #         response_str = record.tti_lims_api_response or ''
    #         if isinstance(response_data, list):
    #             response_str += '\n'.join(
    #                 f'{str(key).ljust(30)} \t{value},'  # Adjust padding dynamically
    #                 for data in response_data if isinstance(data, dict)
    #                 for key, value in data.items()
    #             ) + '\n'
    #         else:
    #             response_str += str(response_data) + '\n'
    #
    #         response_str += '_' * 150 + '\n\n'  # Ensures a clean separator
    #         record.write({'tti_lims_api_response': response_str})
    #
    #
    #
    #     except Exception as e:
    #         values = "Error sending API request: %s" % str(e)
    #         _logger.error(values)
    #         raise UserError(values)
    #     return True

    tti_so_lims_tests_status_count = fields.Integer(string="SO LIMS Tests Status Count",
                                                    compute="_compute_tti_so_lims_tests_status_count")

    def _compute_tti_so_lims_tests_status_count(self):
        for order in self:
            order.tti_so_lims_tests_status_count = self.env['tti.so.lims.tests.status.logs'].search_count(
                [
                    '|',
                    ('sale_order_id', '=', order.id),
                    ('order_id', '=', order.id),
                ]
            )

    def action_view_tti_so_lims_tests_status(self):
        self.ensure_one()
        return {
            'name': _("Lims Tests Status Logs"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'domain': ['|', ('sale_order_id', '=', self.id), ('order_id', '=', self.id)],
            'search_view_id': [self.env.ref('visio_tti_so_customize.view_tti_lims_tests_status_logs_search').id,
                               'search'],
            'views': [[self.env.ref('visio_tti_so_customize.view_tti_lims_tests_status_logs_tree').id, 'list']],
            'res_model': 'tti.so.lims.tests.status.logs',
        }

    tti_test_report_line_ids = fields.One2many(
        comodel_name='tti.test.report.so.line',
        inverse_name='order_id',
        string="Test Report SO Lines",
        copy=False, auto_join=True,
        store=True)
    # compute="_compute_tti_test_report_so_line_ids",

    grand_total = fields.Float(string="Grand Total Price", compute='_compute_grand_total', readonly=True, store=True)

    tti_so_component_breakdown_ids = fields.One2many(
        comodel_name='tti.so.component.breakdown',
        inverse_name='order_id',
        string="SO Component Breakdown Ids",
        copy=True, auto_join=True,
        domain="[('company_id', '=', company_id)]",
    )

    tti_express_charges = fields.Monetary(string="Express Charges")
    tti_express_charges_prcnt = fields.Float(string="Express Charges Percent", default=0.0)
    tti_shuttle_service_charges = fields.Monetary(string="Shuttle Service Charges")
    tti_shuttle_service_charges_prcnt = fields.Float(string="Shuttle Service Charges Percent", default=0.0)
    tti_import_duty_charges = fields.Monetary(string="Import Duty Charges")
    tti_import_duty_charges_prcnt = fields.Float(string="Import Duty Charges Percent", default=0.0)
    tti_courier_charges = fields.Monetary(string="Courier Charges")
    tti_courier_charges_prcnt = fields.Float(string="Courier Charges Percent", default=0.0)
    tti_travelling_charges = fields.Monetary(string="Travelling Charges")
    tti_travelling_charges_prcnt = fields.Float(string="Travelling Charges Prcent", default=0.0, store=True)

    total_taxble_amount = fields.Monetary(string="Total Taxable Amount", compute="compute_total_taxable_amount")

    tti_total_charges = fields.Monetary(string="Total Charges", compute='_compute_all_charges', store=True)

    @api.depends('order_line', 'order_line.default_code')
    def compute_total_taxable_amount(self):
        for order in self:
            lines = order.order_line.filtered(lambda l: l.default_code)
            if lines:
                for line in lines:
                    order.total_taxble_amount += line.price_subtotal + line.price_tax
            else:
                order.total_taxble_amount = 0

    # 111
    @api.depends('order_line', 'tti_express_charges', 'tti_shuttle_service_charges', 'tti_import_duty_charges',
                 'tti_courier_charges', 'tti_travelling_charges')
    def _compute_all_charges(self):
        charges_products = {
            'Express Charges': self.tti_express_charges,
            'Shuttle Service Charges': self.tti_shuttle_service_charges,
            'Import Duty Charges': self.tti_import_duty_charges,
            'Courier Charge': self.tti_courier_charges,
            'Travelling Charges': self.tti_travelling_charges,
        }
        for record in self:
            try:
                record.tti_total_charges = record.tti_express_charges + record.tti_shuttle_service_charges + record.tti_import_duty_charges + record.tti_courier_charges + record.tti_travelling_charges
                for charge_name, charge_value in charges_products.items():
                    charges_product = self.env['product.template'].sudo().search(
                        [('name', '=', charge_name), ('type', '=', 'service')], limit=1)
                    if not charges_product:
                        charges_product = self.env['product.template'].sudo().create({
                            'name': charge_name,
                            'type': 'service',
                            'list_price': 0,
                            'purchase_ok': True,
                            'sale_ok': True,
                        })
                    charges_product_line = record.order_line.filtered(
                        lambda line: line.product_template_id == charges_product)
                    if not charges_product_line:
                        if charge_value != 0:
                            record.order_line = [Command.create({
                                'product_id': charges_product.product_variant_id.id,
                                'name': charge_name,
                                'price_unit': charge_value,
                                'product_uom_qty': 1,
                                'order_id': record.id,
                            })]
                    else:
                        dict_order_line = {
                            'product_uom_qty': 1,
                            'price_unit': charge_value,
                        }
                        charges_product_line.sudo().write(dict_order_line)

            except Exception as e:
                record.tti_total_charges = 0
                _logger.error(f"Error computing total charges: {e}")

    # @api.depends('order_line', 'tti_express_charges', 'tti_shuttle_service_charges', 'tti_import_duty_charges', 'tti_courier_charges', 'tti_travelling_charges')
    # def _compute_all_charges(self):
    #     for record in self:
    #         try:
    #             record.tti_total_charges = record.tti_express_charges + record.tti_shuttle_service_charges + record.tti_import_duty_charges + record.tti_courier_charges + record.tti_travelling_charges
    #             charges_product = self.env['product.template'].sudo().search([('name', '=', 'Charges'), ('type', '=', 'service')], limit=1)
    #             if not charges_product:
    #                 charges_product = self.env['product.template'].sudo().create({
    #                     'name': 'Charges',
    #                     'type':'service',
    #                     'list_price': 0,
    #                     'purchase_ok': True,
    #                     'sale_ok': True,
    #                 })
    #             charges_product_line = record.order_line.filtered(lambda line: line.product_template_id == charges_product)
    #             if not charges_product_line:
    #                 if record.tti_total_charges != 0:
    #                     record.order_line = [Command.create({
    #                         'product_id': charges_product.product_variant_id.id,
    #                         'name': 'Charges',
    #                         'price_unit': record.tti_total_charges,
    #                         'product_uom_qty': 1,
    #                         'order_id': record.id,
    #                     })]
    #             else:
    #                 dict_order_line = {
    #                     'product_uom_qty': 1,
    #                     'price_unit': record.tti_total_charges,
    #                 }
    #                 charges_product_line.sudo().write(dict_order_line)
    #
    #         except Exception as e:
    #             record.tti_total_charges = 0
    #             _logger.error(f"Error computing total charges: {e}")

    @api.depends('tti_test_report_line_ids', 'tti_test_report_line_ids.total_cost', 'tti_test_report_line_ids.qty',
                 'tti_test_report_line_ids.test_report')
    def _compute_grand_total(self):
        for record in self:
            record.grand_total = sum(record.tti_test_report_line_ids.mapped('total_cost'))

    def _add_test_report_lines_from_package(self, package_line):
        test_report_ids = package_line.product_id.product_tmpl_id.test_report_ids
        list_dict_test = []
        for test_pro in test_report_ids:
            test_pro_list_price = test_pro.test_report.list_price
            if self.pricelist_id:
                test_pro_list_price = self.pricelist_id._get_product_price(
                    test_pro.test_report,
                    1.0,
                    currency=self.pricelist_id.currency_id,
                    uom=test_pro.uom_id,
                    date=self.date_order or fields.Date.today(),
                )
            dict_test = {
                "default_code": test_pro.test_report.default_code,
                "test_report": test_pro.test_report.id,
                "package_id": test_pro.product_id.id,
                "package_line_id": package_line.id,  # ✅ link to the specific order line
                "name": test_pro.test_report.tti_test_method,
                "qty": test_pro.qty,
                "list_price": test_pro_list_price,
                "list_price_usd": test_pro.test_report.list_price_usd,
                "test_type": test_pro.test_report.test_type,
                "order_id": self.id,
            }
            list_dict_test.append((0, 0, dict_test))
        self.write({
            "tti_test_report_line_ids": list_dict_test
        })

    def _remove_test_report_lines_from_package(self, package_line):
        lines_to_remove = self.tti_test_report_line_ids.filtered(
            lambda l: l.package_line_id.id == package_line.id
        )
        lines_to_remove.unlink()

    # @api.depends('order_line', 'order_line.product_id')
    # def _compute_tti_test_report_so_line_ids(self):
    #     for order in self:
    #         if len(order.order_line) > 0:
    #             try:
    #                 package = order.order_line.filtered(
    #                     lambda x: x.product_id.product_tmpl_id.test_type == 'test_package')
    #                 test_report_ids = package.mapped("product_id.product_tmpl_id.test_report_ids")
    #                 if len(test_report_ids) > 0:
    #                     list_dict_test = []
    #                     for test_pro in test_report_ids:
    #                         test_pro_list_price = test_pro.test_report.list_price
    #                         if order.pricelist_id:
    #                             test_pro_list_price = order.pricelist_id._get_product_price(
    #                                 test_pro.test_report,
    #                                 1.0,
    #                                 currency=order.pricelist_id.currency_id,
    #                                 uom=test_pro.uom_id,
    #                                 date=order.date_order or fields.Date.today(),
    #                             )
    #                         dict_test = {
    #                             "default_code": test_pro.test_report.default_code,
    #                             "test_report": test_pro.test_report.id,
    #                             "package_id": test_pro.product_id.id,
    #                             "name": test_pro.test_report.tti_test_method,
    #                             "qty": test_pro.qty,
    #                             "list_price": test_pro_list_price,
    #                             "list_price_usd": test_pro.test_report.list_price_usd,
    #                             "test_type": test_pro.test_report.test_type,
    #                             "order_id": order.id,
    #                         }
    #                         list_dict_test.append((0, 0, dict_test))
    #                     order.tti_test_report_line_ids = False
    #                     order.sudo().write({
    #                         "tti_test_report_line_ids": list_dict_test
    #                     })
    #                 else:
    #                     order.tti_test_report_line_ids = False
    #             except Exception as e:
    #                 order.tti_test_report_line_ids = False
    #                 _logger.error(f"Error computing test report line ids: {e}")
    #                 continue
    #         else:
    #             order.tti_test_report_line_ids = False

    def action_generate_tti_so_component_breakdown_ids(self):
        self.ensure_one()
        try:
            _logger.info("Starting generation of TTI SO component breakdown IDs.")
            if self.state != 'draft':
                raise ValidationError("Sale Order Component Breakdown only generated in draft state.")

            # Clear existing breakdowns
            self.tti_so_component_breakdown_ids = None

            tti_no_of_samples = abs(self.tti_no_of_samples)  # Dynamic sample count (A, B, C, etc.)
            tti_no_of_material = abs(self.tti_no_of_material)  # Dynamic material count (1, 2, 3, etc.)

            if tti_no_of_samples >= 27 or tti_no_of_samples >= 27:
                _logger.error("Sample count exceeds 26, which is not supported by the current system.")
                raise ValidationError("Sample count exceeds 26, which is not supported by the current system.")

            list_dict_test = []
            counter_index = 0

            # Using string.ascii_uppercase to get A, B, C, etc.
            sample_letters = list(string.ascii_uppercase)[:tti_no_of_samples]

            for sample_letter in sample_letters:
                for material_num in range(1, tti_no_of_material + 1):
                    counter_index += 1
                    dict_test = {
                        "name": f'Component breakdown {sample_letter}-{material_num} of Sale Order {self.name}',
                        "sequence": counter_index,
                        "tti_sample": f"{sample_letter}",
                        "tti_material_no": f"{sample_letter}{material_num}",
                        "order_id": self.id,
                    }
                    _logger.info(f"Generated component: {dict_test}")
                    list_dict_test.append((0, 0, dict_test))

            # Write new breakdowns
            self.sudo().write({
                "tti_so_component_breakdown_ids": list_dict_test
            })
            _logger.info("Successfully generated TTI SO component breakdown IDs.")

        except Exception as e:
            self.tti_so_component_breakdown_ids = False
            _logger.error(f"Error computing TTI SO component breakdown IDs: {e}", exc_info=True)
            raise ValidationError(f"Error computing TTI SO component breakdown IDs: {e}")

        return True

    # Client/Sample Info
    tti_reference_no = fields.Char(string='Reference No')
    tti_parcel_id = fields.Many2many('tti.parcels', string='Parcels', domain="[('company_id', '=', company_id)]",
                                     copy=False)

    def action_open_tti_parcel_ids(self):
        self.ensure_one()
        return {
            'name': _("Parcels"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'domain': [('id', 'in', self.tti_parcel_id.ids)],
            'search_view_id': [self.env.ref('visio_tti_so_customize.view_tti_parcels_search').id, 'search'],
            'views': [[self.env.ref('visio_tti_so_customize.view_tti_parcels_list').id, 'list'],
                      [self.env.ref('visio_tti_so_customize.view_tti_parcels_form').id, 'form']],
            'res_model': 'tti.parcels',
        }

    tti_date_order_search = fields.Datetime(string=' Search Date')
    tti_currency_from = fields.Many2one('res.currency', string='Tti Currency',
                                        default=lambda self: self.env.company.currency_id, )

    # @api.onchange('tti_currency_from')
    # def _onchange_tti_currency_from(self):
    #     for order in self:
    #         if order.tti_currency_from and order.pricelist_id:
    #             print("updating")
    #             order.pricelist_id.currency_id = order.tti_currency_from
    #             self.action_update_prices()

    tti_exchange_rate = fields.Float(
        compute='_compute_tti_exchange_rate',
        string="Exchange Rate",
        digits=0,
        readonly=True,
        help='Exchange Rate',
        store=True,
    )
    tti_dollar_exchange_rate = fields.Float(
        compute='_compute_current_tti_dollar_exchange_rate',
        string="Dollar Exchange Rate",
        digits=0,
        readonly=True,
        store=True,
        help='Dollar Exchange Rate'
    )

    @api.depends('currency_id', )
    def _compute_current_tti_dollar_exchange_rate(self):
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        for record in self:
            if record.currency_id and usd_currency:
                rate = usd_currency._get_conversion_rate(usd_currency, record.currency_id, record.company_id,
                                                         record.date_order or fields.Date.today())
                print("rate is ", rate)
                record.tti_dollar_exchange_rate = rate
            else:
                record.tti_dollar_exchange_rate = 0.0

    tti_copy_from = fields.Char(string='Copy From')

    @api.depends('tti_currency_from')
    def _compute_tti_exchange_rate(self):
        usd_currency = self.env.ref('base.USD')
        date = self._context.get('date') or fields.Date.context_today(self)
        company = self.env.company

        for rec in self:
            if not rec.tti_currency_from:
                rec.tti_exchange_rate = 0.0
                continue

            # If USD selected, rate is 1
            if rec.tti_currency_from.id == usd_currency.id:
                rec.tti_exchange_rate = 1.0
            else:
                # Get how much 1 USD is in the selected currency
                rate = rec.tti_currency_from._get_conversion_rate(
                    from_currency=usd_currency,
                    to_currency=rec.tti_currency_from,
                    company=company,
                    date=date
                )
                rec.tti_exchange_rate = rate

    # @api.depends('tti_currency_from')
    # def _compute_tti_exchange_rate(self):
    #     date = self._context.get('date') or fields.Date.context_today(self)
    #     company = self.env['res.company'].sudo().browse(self._context.get('company_id')) or self.env.company
    #     company_currency = company.currency_id
    #     to_currency = self.tti_currency_from
    #     currency_rates = (company_currency + to_currency)._get_rates(self.env.company, date)
    #     if currency_rates and to_currency:
    #         currency_rate = (currency_rates.get(company_currency.id) or 1.0) / currency_rates.get(to_currency.id)
    #         self.sudo().write({
    #             'tti_exchange_rate': currency_rate
    #         })

    # @api.depends_context('to_currency', 'date', 'company', 'company_id')
    # def _compute_current_tti_dollar_exchange_rate(self):
    #     date = self._context.get('date') or fields.Date.context_today(self)
    #     company = self.env['res.company'].sudo().browse(self._context.get('company_id')) or self.env.company
    #     company_currency = company.currency_id
    #     to_currency = self.env['res.currency'].sudo().search([('name', '=', 'PKR')])
    #     currency_rates = (company_currency + to_currency)._get_rates(self.env.company, date)
    #     if currency_rates and to_currency:
    #         currency_rate = (currency_rates.get(company_currency.id) or 1.0) / currency_rates.get(to_currency.id)
    #         self.sudo().write({
    #             'tti_dollar_exchange_rate': currency_rate
    #         })

    # Party Information
    # 1st Column
    tti_pi_manufacturer = fields.Many2one('res.partner', domain=[('tti_company_category', '=', 'manufacture')],
                                          string='Manufacturer')
    tti_pi_applicant = fields.Many2one('res.partner', domain=[('tti_company_category', '=', 'applicant')],
                                       string='Applicant')
    tti_pi_agent_id = fields.Many2one('res.partner', string='Agent', domain=[('tti_company_category', '=', 'agent')], )
    tti_pi_report_to = fields.Char(string='Report To Dep')
    tti_pi_report_to_manufacturer = fields.Many2one(
        'res.partner',
        domain=[('tti_company_category', '=', 'manufacture')],
        string='Report To'
    )
    tti_pi_to_report = fields.Selection([('manufacturer', 'Manufacturer'), ('brand', 'Brand')], string='Report To Selection')

    # 2nd Column
    tti_pi_address = fields.Char(string='Address')
    tti_pi_buyer = fields.Many2one('res.partner', domain=[('tti_company_category', '=', 'buyer')], string='Buyer')
    tti_pi_buyer_test_packages = fields.Many2many('product.template', related='tti_pi_buyer.tti_test_packages',
                                                  readonly=True)
    tti_pi_email_cc = fields.Char(string='CC')
    tti_pi_email = fields.Char(
        string='Email',
        # compute="_compute_tti_pi_email",
        # store=True,
        readonly=True
    )

    # @api.depends('tti_pi_to_report', )
    # def _compute_tti_pi_email(self):
    #     for record in self:
    #         if record.tti_pi_to_report == 'manufacturer' and record.partner_id and record.partner_id.email:
    #             record.tti_pi_email = f"{record.partner_id.email}"
    #         elif record.tti_pi_to_report == 'brand' and record.tti_pi_brand_id and record.tti_pi_brand_id.email:
    #             record.tti_pi_email = f"{record.tti_pi_brand_id.email}"
    #         else:
    #             record.tti_pi_email = ''

    # 3rd Column
    tti_pi_code = fields.Char(string='Zone', copy=False)
    tti_pi_brand_id = fields.Many2one('res.partner', domain=[('tti_company_category', '=', 'brand')], string='Brand', )
    tti_pi_submitted_by = fields.Char(string='Submitted By')

    # Sample Information
    # 1st Column
    tti_si_category = fields.Many2one('tti.si.category', string='Category', domain="[('company_id', '=', company_id)]")
    category_type = fields.Selection(related='tti_si_category.category_type', readonly=False, store=True)
    tti_si_end_use = fields.Char(string='End Use')
    tti_si_fiber = fields.Many2one('tti.si.fiber', string='Fiber', domain="[('company_id', '=', company_id)]")
    tti_fiber_si = fields.Text(string='Fiber')
    # ------------------------conditioned------------------------
    tti_si_design = fields.Char(string='Design')
    tti_si_order_qty = fields.Char(string='Order QTY')
    # -----------------------------------------------------------
    tti_si_po = fields.Char(string='PO')
    tti_si_dye_stuff = fields.Many2one('tti.si.dye.stuff', string='Dye Stuff',
                                       domain="[('company_id', '=', company_id)]")
    tti_si_size = fields.Char(string='Size')
    tti_si_protocol = fields.Char(string='Protocol')
    tti_si_p_report = fields.Char(string='P Report')
    tti_si_care_inst = fields.Char(string='Care Instructions')

    # 2nd Column
    tti_si_sub_category = fields.Many2one('tti.si.sub.category',
                                          domain="[('tti_si_category', '=', tti_si_category) , ('company_id', '=', company_id)]",
                                          string='Sub Category')
    tti_si_product_type = fields.Many2one('tti.si.product.type',
                                          domain="[('tti_si_category', '=', tti_si_category) , ('company_id', '=', company_id)]",
                                          string='Product Type')

    @api.onchange('tti_si_category')
    def _onchange_tti_si_category(self):
        self.tti_si_sub_category = False
        self.tti_si_product_type = False

    # ------------------------conditioned------------------------
    tti_si_material = fields.Char(string='Material')
    tti_si_fabric = fields.Char(string='Fabric')
    # -----------------------------------------------------------
    tti_si_style_no = fields.Char(string='Style No')
    tti_si_colour = fields.Char(string='Colour')
    tti_si_destination = fields.Many2one('res.country', string='Destination')
    tti_si_test_no = fields.Char(string='Test No')
    tti_si_season = fields.Char(string='Season')
    tti_si_product_category = fields.Many2one('product.category', string='Product Category')
    tti_si_product_category_text = fields.Char(string='Product Category')
    tti_si_partner = fields.Many2one('res.partner', string='Partner Old')
    tti_si_select_partner = fields.Selection(
        [('tti_testing', 'Tti Testing'), ('mts', 'MTS')],
        string='Partner',
        default='tti_testing',
        tracking=True,
    )

    # 3rd Column
    tti_si_description = fields.Char(string='Description')
    # ------------------------conditioned------------------------
    tti_si_weight = fields.Float(string='Weight')
    tti_si_code = fields.Float(string='Tti Code', copy=False)
    # -----------------------------------------------------------
    tti_si_uom = fields.Many2one('tti.si.uom', string='UOM', domain="[('company_id', '=', company_id)]")
    # ------------------------conditioned------------------------
    tti_si_construction = fields.Char(string='Construction')
    tti_si_model_no = fields.Char(string='Model No')
    # -----------------------------------------------------------
    # ------------------------conditioned------------------------
    tti_si_style = fields.Char(string='Style')
    tti_si_article_no = fields.Char(string='Article No')
    # -----------------------------------------------------------
    tti_si_program = fields.Many2one('tti.si.program', string='Program', domain="[('company_id', '=', company_id)]")
    tti_si_origin = fields.Many2one('res.country', string='Origin')
    # ------------------------conditioned------------------------

    tti_si_dosage_form = fields.Many2one('tti.si.dosage.form', string='Dosage Form',
                                         domain="[('company_id', '=', company_id)]")
    tti_si_manufacturer = fields.Char(string='Manufacturer')
    tti_si_sampling_date = fields.Date(string='Sampling Date')

    tti_si_department = fields.Many2one('tti.si.department', string='Department',
                                        domain="[('company_id', '=', company_id)]")
    tti_si_dept = fields.Text(string='Department')
    tti_si_article_name = fields.Char(string='Article Name')
    # -----------------------------------------------------------
    tti_si_vr_no = fields.Char(string='VR No')
    tti_si_sp_inst = fields.Char(string='Special Instructions')

    tti_si_label_1_name = fields.Char(string='Label 1 Name')
    tti_si_label_1_value = fields.Char(string='Label 1 Value')

    tti_si_label_2_name = fields.Char(string='Label 2 Name')
    tti_si_label_2_value = fields.Char(string='Label 2 Value')

    tti_si_label_3_name = fields.Char(string='Label 3 Name')
    tti_si_label_3_value = fields.Char(string='Label 3 Value')

    tti_si_label_4_name = fields.Char(string='Label 4 Name')
    tti_si_label_4_value = fields.Char(string='Label 4 Value')

    # Contact Information
    tti_ci_mobile_no = fields.Char(string='Mobile No')
    tti_ci_email1 = fields.Char(string='Email 1')
    tti_ci_email2 = fields.Char(string='Email 2')
    tti_ci_email3 = fields.Char(string='Email 3')
    tti_ci_email4 = fields.Char(string='Email 4')
    tti_ci_email5 = fields.Char(string='Email 5')
    tti_ci_email6 = fields.Char(string='Email 6')

    # Image Upload
    tti_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string="Images",
        copy=False,
    )

    # Care Label Upload
    tti_care_label_image_one_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False,
                                                  string="Care Label 1 Attachment", )
    tti_care_label_image_two_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False,
                                                  string="Care Label 2 Attachment", )
    tti_care_label_image_three_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False,
                                                    string="Care Label 3 Attachment", )
    tti_care_label_image_four_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False,
                                                   string="Care Label 4 Attachment", )
    tti_care_label_image_five_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False,
                                                   string="Care Label 5 Attachment", )
    tti_care_label_image_six_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False,
                                                  string="Care Label 6 Attachment", )

    tti_care_label_image_one_name = fields.Char(related='tti_care_label_image_one_id.name', readonly=False,
                                                string="Care Label 1 Image Name", copy=False)
    tti_care_label_image_two_name = fields.Char(related='tti_care_label_image_two_id.name', readonly=False,
                                                string="Care Label 2 Image Name", copy=False)
    tti_care_label_image_three_name = fields.Char(related='tti_care_label_image_three_id.name', readonly=False,
                                                  string="Care Label 3 Image Name", copy=False)
    tti_care_label_image_four_name = fields.Char(related='tti_care_label_image_four_id.name', readonly=False,
                                                 string="Care Label 4 Image Name", copy=False)
    tti_care_label_image_five_name = fields.Char(related='tti_care_label_image_five_id.name', readonly=False,
                                                 string="Care Label 5 Image Name", copy=False)
    tti_care_label_image_six_name = fields.Char(related='tti_care_label_image_six_id.name', readonly=False,
                                                string="Care Label 6 Image Name", copy=False)

    tti_care_label_image_one = fields.Binary(related='tti_care_label_image_one_id.datas', related_sudo=True,
                                             readonly=False, prefetch=False, string="Care Label 1", copy=False)
    tti_care_label_image_two = fields.Binary(related='tti_care_label_image_two_id.datas', related_sudo=True,
                                             readonly=False, prefetch=False, string="Care Label 2", copy=False)
    tti_care_label_image_three = fields.Binary(related='tti_care_label_image_three_id.datas', related_sudo=True,
                                               readonly=False, prefetch=False, string="Care Label 3", copy=False)
    tti_care_label_image_four = fields.Binary(related='tti_care_label_image_four_id.datas', related_sudo=True,
                                              readonly=False, prefetch=False, string="Care Label 4", copy=False)
    tti_care_label_image_five = fields.Binary(related='tti_care_label_image_five_id.datas', related_sudo=True,
                                              readonly=False, prefetch=False, string="Care Label 5", copy=False)
    tti_care_label_image_six = fields.Binary(related='tti_care_label_image_six_id.datas', related_sudo=True,
                                             readonly=False, prefetch=False, string="Care Label 6", copy=False)

    # Component Breakdown
    tti_okeo_image_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False,
                                        string="OKEO Image Attachment", )
    tti_okeo_image = fields.Binary(related='tti_okeo_image_id.datas', related_sudo=True, readonly=False, prefetch=False,
                                   string="OKEO Image", copy=False)
    tti_okeo_image_name = fields.Char(related='tti_okeo_image_id.name', readonly=False, string="OKEO Image Name",
                                      copy=False)

    tti_image_comp_breakdown_id = fields.Many2one('ir.attachment', ondelete='cascade', auto_join=True, copy=False,
                                                  string="Image Attachment")
    tti_image_comp_breakdown = fields.Binary(related='tti_image_comp_breakdown_id.datas', related_sudo=True,
                                             readonly=False, prefetch=False, string="Image", copy=False)
    tti_image_comp_breakdown_name = fields.Char(related='tti_image_comp_breakdown_id.name', readonly=False,
                                                string="Breakdown Image Name")

    def _validate_image_attachments(self):
        allowed_mime_types = ['image/png', 'image/jpeg']
        allowed_extensions = ['png', 'jpg', 'jpeg']

        # List of Many2one attachment fields
        attachment_fields = [
            'tti_care_label_image_one_id',
            'tti_care_label_image_two_id',
            'tti_care_label_image_three_id',
            'tti_care_label_image_four_id',
            'tti_care_label_image_five_id',
            'tti_care_label_image_six_id',
            'tti_okeo_image_id',
            'tti_image_comp_breakdown_id',
        ]

        for record in self:
            # Validate Many2one fields
            for field_name in attachment_fields:
                attachment = getattr(record, field_name)
                if attachment:
                    if attachment.mimetype not in allowed_mime_types:
                        raise ValidationError(
                            f"Invalid image format for field '{field_name.replace('_', ' ').title()}'. "
                            "Only PNG, JPG, and JPEG formats are allowed."
                        )

            # Validate Many2many attachments
            for attachment in record.tti_attachment_ids:
                if attachment.mimetype not in allowed_mime_types:
                    raise ValidationError(
                        f"Invalid format in Images field. Only PNG, JPG, and JPEG formats are allowed."
                    )

    tti_no_of_samples = fields.Integer(string="No of Samples", copy=False)
    tti_no_of_material = fields.Integer(string="No of Material", copy=False)
    tti_remarks = fields.Text(string="Remarks", copy=False)

    acknowledgement_email_list = fields.Char(compute='_compute_acknowledgement_emails')

    @api.depends('sale_email_ids.emails_to_receive', 'sale_email_ids.email')
    def _compute_acknowledgement_emails(self):
        for record in self:
            if record.sale_email_ids:
                filtered_emails = record.sale_email_ids.filtered(
                    lambda e: e.emails_to_receive in ('all', 'acknowledgment_to')
                )
                record.acknowledgement_email_list = ','.join(filtered_emails.mapped('email'))
            else:
                record.acknowledgement_email_list = False

    def _create_ir_attachment(self, name, datas):
        attachment_list = []
        attachment_list.append({
            'name': name or f'{self.name} - attachment',
            'type': 'binary',
            'public': True,
            'datas': datas,
            'res_model': self._name,
            'res_id': self.id
        })
        attachment_id = self.env['ir.attachment'].sudo().create(attachment_list)
        return attachment_id.id or False

    def process_image(self, vals, image_key, name_key, attachment_key):
        if image_key in vals and name_key in vals:
            image_name = vals.get(name_key)
            image = vals.get(image_key)
            vals[attachment_key] = self._create_ir_attachment(image_name, image) if image and image_name else False
            if image:
                image_binary = base64.b64decode(image)
                resized_image_binary = image_tools.image_process(
                    image_binary,
                    size=(600, 400),
                    verify_resolution=True
                )
                vals[image_key] = base64.b64encode(resized_image_binary) if resized_image_binary else False

    def unlink(self):
        if not self.env.user.has_group('visio_tti_so_customize.group_delete_so'):
            raise AccessError(_("You are not allowed to delete Sale Orders."))

        return super(SaleOrder, self).unlink()

    @api.model_create_multi
    def create(self, list_vals):
        try:
            for vals in list_vals:
                self.process_image(vals, 'tti_okeo_image', 'tti_okeo_image_name', 'tti_okeo_image_id')
                self.process_image(vals, 'tti_care_label_image_one', 'tti_care_label_image_one_name',
                                   'tti_care_label_image_one_id')
                self.process_image(vals, 'tti_care_label_image_two', 'tti_care_label_image_two_name',
                                   'tti_care_label_image_two_id')
                self.process_image(vals, 'tti_care_label_image_three', 'tti_care_label_image_three_name',
                                   'tti_care_label_image_three_id')
                self.process_image(vals, 'tti_care_label_image_four', 'tti_care_label_image_four_name',
                                   'tti_care_label_image_four_id')
                self.process_image(vals, 'tti_care_label_image_five', 'tti_care_label_image_five_name',
                                   'tti_care_label_image_five_id')
                self.process_image(vals, 'tti_care_label_image_six', 'tti_care_label_image_six_name',
                                   'tti_care_label_image_six_id')
                self.process_image(vals, 'tti_image_comp_breakdown', 'tti_image_comp_breakdown_name',
                                   'tti_image_comp_breakdown_id')

                # if vals.get('name', _("New")) == _("New") and vals.get('tti_si_select_partner') == 'mts':
                #     seq_date = fields.Datetime.context_timestamp(
                #         self, fields.Datetime.to_datetime(vals['date_order'])
                #     ) if 'date_order' in vals else None
                #     sequence_number = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(
                #         'mts.sale.order', sequence_date=seq_date) or _("New")
                #     vals['name'] = sequence_number


        except Exception as e:
            raise ValueError(f"An error occurred while create sale order: {str(e)}")
        res = super().create(list_vals)
        self._validate_image_attachments()
        # try:
        #     if res.tti_currency_from:
        #         target_currency = res.currency_id or self.env.company.currency_id
        #         to_currency = res.tti_currency_from
        #         company = res.company_id
        #         date_today = fields.Date.context_today(self.env.user)
        #         conversion_rate = self.env['res.currency']._get_conversion_rate(
        #             from_currency=target_currency,
        #             to_currency=to_currency,
        #             company=company,
        #             date=date_today,
        #         )
        #         res.tti_exchange_rate = conversion_rate
        #         # for line in res.order_line:
        #         #     line.price_unit = (res.tti_exchange_rate * line.price_unit_origin)
        # except Exception as e:
        #     raise ValueError(f"An error occurred while updating sale order: {str(e)}")

        try:
            for tti_attachment_id in res.tti_attachment_ids:
                attachment_ids_dict = {
                    "public": True,
                }
                image = tti_attachment_id.datas
                if image:
                    image_binary = base64.b64decode(image)
                    resized_image_binary = image_tools.image_process(
                        image_binary,
                        size=(600, 400),
                        verify_resolution=True
                    )
                    new_image = base64.b64encode(resized_image_binary) if resized_image_binary else False
                    if new_image:
                        attachment_ids_dict['datas'] = new_image
                tti_attachment_id.write(attachment_ids_dict)
        except Exception as e:
            raise ValueError(f"An error occurred while updating sale order: {str(e)}")
        return res

    def write(self, vals):

        try:
            self.process_image(vals, 'tti_okeo_image', 'tti_okeo_image_name', 'tti_okeo_image_id')
            self.process_image(vals, 'tti_care_label_image_one', 'tti_care_label_image_one_name',
                               'tti_care_label_image_one_id')
            self.process_image(vals, 'tti_care_label_image_two', 'tti_care_label_image_two_name',
                               'tti_care_label_image_two_id')
            self.process_image(vals, 'tti_care_label_image_three', 'tti_care_label_image_three_name',
                               'tti_care_label_image_three_id')
            self.process_image(vals, 'tti_care_label_image_four', 'tti_care_label_image_four_name',
                               'tti_care_label_image_four_id')
            self.process_image(vals, 'tti_care_label_image_five', 'tti_care_label_image_five_name',
                               'tti_care_label_image_five_id')
            self.process_image(vals, 'tti_care_label_image_six', 'tti_care_label_image_six_name',
                               'tti_care_label_image_six_id')
            self.process_image(vals, 'tti_image_comp_breakdown', 'tti_image_comp_breakdown_name',
                               'tti_image_comp_breakdown_id')


            if not vals.get('quotation_num') and (not self.quotation_num or self.quotation_num == 'New'):
                vals['quotation_num'] = self.name

            # if vals.get('tti_si_select_partner') == 'mts':
            #     seq_date = fields.Datetime.context_timestamp(
            #         self, fields.Datetime.to_datetime(vals['date_order'])
            #     ) if 'date_order' in vals else None
            #     vals['name'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(
            #         'mts.sale.order', sequence_date=seq_date) or _("New")

            # Define all charge fields and their corresponding percentage fields
            charge_fields_mapping = {
                'tti_express_charges': 'tti_express_charges_prcnt',
                'tti_shuttle_service_charges': 'tti_shuttle_service_charges_prcnt',
                'tti_import_duty_charges': 'tti_import_duty_charges_prcnt',
                'tti_courier_charges': 'tti_courier_charges_prcnt',
                'tti_travelling_charges': 'tti_travelling_charges_prcnt'
            }

            # Calculate either charge or percentage based on which field was updated
            for charge_field, percent_field in charge_fields_mapping.items():
                if charge_field in vals:
                    # Charge value was provided - calculate percentage
                    for record in self:
                        if record.total_taxble_amount > 0:
                            vals[percent_field] = round((vals[charge_field] / record.total_taxble_amount), 2)
                        else:
                            vals[percent_field] = 0.0
                elif percent_field in vals:
                    # Percentage was provided - calculate charge value
                    for record in self:
                        vals[charge_field] = round(vals[percent_field] * record.total_taxble_amount, 2)

            # if vals.get('tti_si_select_partner') == 'tti_testing' and self.tti_si_select_partner == 'mts':
            #     seq_date = fields.Datetime.context_timestamp(
            #         self, fields.Datetime.to_datetime(vals['date_order'])
            #     ) if 'date_order' in vals else None
            #     vals['name'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(
            #         'sale.order', sequence_date=seq_date) or _("New")

        except Exception as e:
            raise ValueError(f"An error occurred while updating sale order: {str(e)}")

        res = super().write(vals)

        self._validate_image_attachments()

        print("yes true0")
        print("vasls" , vals)
        if vals.get('tti_lims_api_response_check'):
            print("yes true")
            try:
                template = self.env.ref('visio_tti_so_customize.mail_template_sale_order')
                pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                    'visio_tti_so_invoice_report.action_custom_sale_report',
                    res_ids=self.ids
                )
                attachment = self.env['ir.attachment'].create({
                    'name': f'Acknowledgement_{self.name}.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf'
                })
                _logger.info(f"Attachment created successfully: {attachment.name} (ID: {attachment.id})")
                if self.acknowledgement_email_list:
                    template.send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'attachment_ids': [(4, attachment.id)]
                        }
                    )
            except Exception as e:
                _logger.error(f"Error in acknowledgement email process for record {self.id}: {str(e)}")

        try:
            pass
        #         if vals.get('tti_currency_from'):
        #             if self.tti_currency_from:
        #                 target_currency = self.currency_id or self.env.company.currency_id
        #                 to_currency = self.tti_currency_from
        #                 company = self.company_id
        #                 date_today = fields.Date.context_today(self.env.user)
        #                 conversion_rate = self.env['res.currency']._get_conversion_rate(
        #                     from_currency=target_currency,
        #                     to_currency=to_currency,
        #                     company=company,
        #                     date=date_today,
        #                 )
        #                 self.tti_exchange_rate = conversion_rate
        except Exception as e:
            raise ValueError(f"An error occurred while updating sale order: {str(e)}")

        if vals.get('tti_attachment_ids'):
            for tti_attachment_id in self.tti_attachment_ids:
                attachment_ids_dict = {
                    "public": True,
                }
                image = tti_attachment_id.datas
                if image:
                    image_binary = base64.b64decode(image)
                    resized_image_binary = image_tools.image_process(
                        image_binary,
                        size=(600, 400),
                        verify_resolution=True
                    )
                    new_image = base64.b64encode(resized_image_binary) if resized_image_binary else False
                    if new_image:
                        attachment_ids_dict['datas'] = new_image
                tti_attachment_id.write(attachment_ids_dict)

        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_unit_rate = fields.Float(string="Dollar Rate", compute="_compute_price_unit_rate", readonly=False, copy=True)

    price_unit_rate_frozen = fields.Float(  # <-- new field
        string="Frozen Dollar Rate",
        default=0.0,
        copy=True
    )

    dollar_exchange_rate = fields.Float(string="Dollar Exchange Rate", related='order_id.tti_dollar_exchange_rate',
                                        readonly=True)
    comments = fields.Char(string="Comments", )
    composites = fields.Char(string="Composites", )
    default_code = fields.Char(related='product_id.default_code', readonly=True)
    test_type = fields.Selection(related='product_id.test_type', readonly=True)
    tti_test_method = fields.Char(related='product_id.tti_test_method', readonly=True)

    user_has_group_tti_enable_so_price = fields.Boolean(
        compute="_compute_user_has_group_tti_enable_so_price",
        default=False
    )
    user_has_group_tti_allow_taxes = fields.Boolean(
        compute="_compute_user_has_group_tti_allow_taxes",
        default=False
    )
    unique_number = fields.Integer(
        string="Old API Global Unique ID",
        readonly=False,
        index=True,
        copy=False,
    )
    new_unique_number = fields.Integer(
        string="New API Global Unique ID",
        readonly=False,
        index=True,
        copy=False,
    )

    @api.depends(
        'product_id', 'product_uom', 'product_uom_qty',
        'price_unit_rate_frozen',
        'order_id.tti_dollar_exchange_rate',
        'order_id.pricelist_id.currency_id'
    )
    def _compute_price_unit(self):
        for line in self:
            # Don't compute the price for deleted lines.
            if not line.order_id:
                continue

            # === Custom branch: if a frozen USD rate exists, convert using order's exchange rate ===
            if line.price_unit_rate_frozen:
                rate = line.order_id.tti_dollar_exchange_rate or 1.0
                currency = line.order_id.pricelist_id.currency_id
                # If SO currency is USD, keep frozen rate as-is; else multiply by exchange rate.
                if currency and currency.name == 'USD':
                    new_price = line.price_unit_rate_frozen
                else:
                    new_price = line.price_unit_rate_frozen * rate

                line.price_unit = new_price
                line.technical_price_unit = new_price
                continue  # Skip default pricing when frozen rate is present

            # Respect manual edits / invoiced amounts / expense policy (same as base).
            if (
                    (line.technical_price_unit != line.price_unit and not line.env.context.get(
                        'force_price_recomputation'))
                    or line.qty_invoiced > 0
                    or (line.product_id.expense_policy == 'cost' and line.is_expense)
            ):
                continue

            line = line.with_context(sale_write_from_compute=True)


            # === Default Odoo logic ===
            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
                line.technical_price_unit = 0.0
            else:
                line = line.with_company(line.company_id)
                price = line._get_display_price()
                line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
                    price,
                    product_taxes=line.product_id.taxes_id.filtered(lambda tax: tax.company_id == line.env.company),
                    fiscal_position=line.order_id.fiscal_position_id,
                )
                line.technical_price_unit = line.price_unit

    # @api.depends('dollar_exchange_rate', 'price_unit', 'price_unit_rate_frozen')
    # def _compute_price_unit_rate(self):
    #     for record in self:
    #         if record.price_unit_rate_frozen:
    #             record.price_unit_rate = record.price_unit_rate_frozen
    #             continue
    #
    #         if record.order_id and record.order_id.pricelist_id and record.order_id.pricelist_id.currency_id.name == 'USD':
    #             record.price_unit_rate = record.price_unit
    #         else:
    #             record.price_unit_rate = record.price_unit / record.dollar_exchange_rate if record.dollar_exchange_rate else 0.0

    @api.depends('dollar_exchange_rate', 'price_unit', 'price_unit_rate_frozen')
    def _compute_price_unit_rate(self):
        for record in self:
            # If frozen rate is set AND price_unit has not been manually changed → use frozen
            if record.price_unit_rate_frozen and not record._origin:
                record.price_unit_rate = record.price_unit_rate_frozen
                continue

            # Otherwise, recalc from price_unit
            if record.order_id and record.order_id.pricelist_id and record.order_id.pricelist_id.currency_id.name == 'USD':
                record.price_unit_rate = record.price_unit
            else:
                record.price_unit_rate = (
                    record.price_unit / record.dollar_exchange_rate
                    if record.dollar_exchange_rate else 0.0
                )

    def copy_data(self, default=None):
        data_list = super().copy_data(default)
        for origin, datum in zip(self, data_list):
            datum['price_unit_rate_frozen'] = origin.price_unit_rate
        return data_list

    @api.model_create_multi
    def create(self, vals_list):
        # sequence = self.env['ir.sequence'].sudo()
        for vals in vals_list:

            if not vals.get('price_unit_rate'):
                order = self.env['sale.order'].browse(vals.get('order_id'))
                currency_name = order.pricelist_id.currency_id.name if order and order.pricelist_id else ''
                rate = order.tti_dollar_exchange_rate or 1.0
                if currency_name == 'USD':
                    vals['price_unit_rate'] = vals.get('price_unit', 0.0)
                else:
                    vals['price_unit_rate'] = vals.get('price_unit', 0.0) / rate if rate else 0.0

            if not vals.get('new_unique_number'):
                new_unique_number = self.env['ir.sequence'].sudo().next_by_code('new.api.global.unique.id')
                # Ensure it's unique
                while self.env['sale.order.line'].sudo().search_count([('new_unique_number', '=', new_unique_number)]):
                    new_unique_number = self.env['ir.sequence'].sudo().next_by_code('new.api.global.unique.id')
                vals['new_unique_number'] = new_unique_number

        lines = super().create(vals_list)
        lines._compute_price_unit()
        for line in lines:
            if line.product_id.product_tmpl_id.test_type == 'test_package':
                line.order_id._add_test_report_lines_from_package(line)

        return lines

    def write(self, vals):
        for line in self:
            old_product = line.product_id
            res = super(SaleOrderLine, line).write(vals)
            new_product = line.product_id

            if 'product_id' in vals:
                order = line.order_id

                if old_product and old_product.product_tmpl_id.test_type == 'test_package':
                    order._remove_test_report_lines_from_package(line)

                if new_product and new_product.product_tmpl_id.test_type == 'test_package':
                    order._add_test_report_lines_from_package(line)
        return res

    def unlink(self):
        for line in self:
            if line.product_id.product_tmpl_id.test_type == 'test_package':
                line.order_id._remove_test_report_lines_from_package(line)
        return super().unlink()

    def _compute_user_has_group_tti_allow_taxes(self):
        has_group = self.env.user.has_group('visio_tti_so_customize.group_tti_allow_taxes')
        for record in self:
            record.user_has_group_tti_allow_taxes = has_group

    def _compute_user_has_group_tti_enable_so_price(self):
        has_group = self.env.user.has_group('visio_tti_so_customize.group_tti_enable_so_price')
        for record in self:
            record.user_has_group_tti_enable_so_price = has_group


class SaleOrderDiscount(models.TransientModel):
    _inherit = 'sale.order.discount'

    def action_apply_discount(self):
        self.ensure_one()

        user_max_discount = self.env.user.discount_percent

        if not user_max_discount:
            raise UserError(_(
                "You dont have any discount authorized limit."
            ))

        if self.discount_percentage > user_max_discount:
            raise UserError(_(
                "Your discount percentage (%.2f%%) exceeds your authorized limit (%.2f%%). "
                % (self.discount_percentage * 100, user_max_discount * 100)
            ))

        return super().action_apply_discount()


class SaleEmails(models.Model):
    _name = "sale.emails"
    _description = "Sale Order Emails"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order", ondelete='cascade')
    email = fields.Char(string="Email")
    emails_to_receive = fields.Selection([
        ('all', 'All Emails'),
        ('report', 'Report Only'),
        ('invoice', 'Invoice Only'),
        ('quotation', 'Quotation Only'),
        ('acknowledgment_to', 'Acknowledgement To')
    ], string="Emails to Receive", default='all')

class MassCancelOrders(models.TransientModel):
    _inherit = 'sale.mass.cancel.orders'

    def action_mass_cancel(self):
        for order in self.sale_order_ids:
            if order.state in ['draft' , 'sent' , 'quotation_done', 'quotation_approved']:
                order._action_cancel()
            else:
                raise ValidationError("Only a quotation can be cancelled, not a sale order.")
