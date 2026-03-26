# quran_academy\visio_contact_extension_qa\models\inherit_res_partner.py
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_member = fields.Boolean(string="Is Member")
    street3_qa = fields.Char(string="Street 3")
    ac_numnber_qa = fields.Integer(string="AC")
    acno_qa = fields.Char(string="Membership No")

    gender_qa = fields.Selection([
        ('m', 'M'),
        ('f', 'F'),
        ('o', 'Other')
    ], string="Gender")

    telno_off = fields.Char(string="Tell No Off")
    ref_name = fields.Char(string="Ref. Name")

    trans_date_qa = fields.Date(string="Last Transaction Date")
    rec_no_qa = fields.Char(string="Rec. No.")
    paid_by_qa = fields.Char(string="Paid By", )

    date_of_pay = fields.Date(string="Date of Pay")
    mem_date = fields.Date(string="Membership Date")
    # ftcontb = fields.Integer(string="FTContb", compute="_compute_ftcontb_amount", store=True)
    ftcontb = fields.Integer(string="First Contribution", store=True)
    mlcontb = fields.Integer(string="Monthly Contribution")

    special = fields.Selection([
        ('default', 'Default'),
        ('hold', 'Hold'),
        ('late', 'Late'),
        ('transferred_mohsinin', 'Transferred to Mohsinin Members'),
        ('transferred_mohsinin_m210', 'Transferred to Mohsinin Members M-210'),
        ('transferred_mohsinin_m574', 'Transferred to Mohsinin Members M-574'),
        ('transferred_permanent', 'Transferred to Permanent Members'),
    ], string="Special")

    ch_rcpt_no = fields.Char(string="Receipt No")
    show_records_qa = fields.Selection([
        ('default', 'Default'),
        ('mohsinin', 'Mohsinin'),
        ('permanent', 'Permanent'),
        ('general', 'General')
    ], string="Contact Type", required=True, default='default')

    employee_qa = fields.Boolean(string="Employee")
    label_hold_yn = fields.Boolean(string="Label Hold Y/N")
    by_hand_qa = fields.Boolean(string="By Hand")

    urdu_lable = fields.Boolean(string="Urdu Lable")
    urdu_name = fields.Char(string="Urdu Name")
    urdu_address = fields.Char(string="Urdu Address")
    urdu_address1 = fields.Char(string="Urdu Address1")
    urdu_address2 = fields.Char(string="Urdu Address2")
    payment_ids = fields.One2many("account.payment", "partner_id", string="Payments", readonly=True, )

    mablagh = fields.Char(string="Mablagh")
    basorat = fields.Char(string="Basorat")
    baabat = fields.Char(string="Baabat")

    city_qacademy = fields.Char(string="City")
    state_qacademy = fields.Char(string="State")
    country_qacademy = fields.Char(string="Country")

    # [Functions ---------------------------------------------]

    # Function for dates "date_of_pay" and "mem_date"
    @api.onchange('date_of_pay')
    def _onchange_date_of_pay(self):
        if not self.date_of_pay:
            self.mem_date = False
        elif not self.mem_date:
            self.mem_date = self.date_of_pay

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Ensure ac_numnber_qa is set
            if not vals.get('ac_numnber_qa'):
                vals['ac_numnber_qa'] = self.env['ir.sequence'] \
                    .sudo() \
                    .next_by_code('res.partner.ac.number.qa')
            # If show_records_qa is provided, prefix acno_qa accordingly
            if vals.get('show_records_qa') and vals.get('ac_numnber_qa'):
                prefix_map = {
                    'general': 'G',
                    'mohsinin': 'M',
                    'permanent': 'P',
                    'default': '',
                }
                prefix = prefix_map.get(vals['show_records_qa'], '')
                vals['acno_qa'] = f"{prefix}{vals['ac_numnber_qa']}"

            vals['is_member'] = True

        return super(ResPartner, self).create(vals_list)

    # Function for ACNO field i.e. comes with the AC number and the Contact Type
    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'show_records_qa' in vals or 'ac_numnber_qa' in vals:
                if rec.show_records_qa and rec.ac_numnber_qa:
                    prefix_map = {
                        'general': 'G',
                        'mohsinin': 'M',
                        'permanent': 'P',
                        'default': ''
                    }
                    prefix = prefix_map.get(rec.show_records_qa, '')
                    rec.acno_qa = f"{prefix}{rec.ac_numnber_qa}"
        return res

    # Function for updating the value
    @api.onchange('show_records_qa')
    def _onchange_show_records_qa(self):
        if self.ac_numnber_qa and self.show_records_qa:
            prefix_map = {
                'general': 'G',
                'mohsinin': 'M',
                'permanent': 'P',
                'default': ''
            }
            prefix = prefix_map.get(self.show_records_qa, '')
            self.acno_qa = f"{prefix}{self.ac_numnber_qa}"

    # @api.depends('payment_ids.date', 'payment_ids.amount')
    # def _compute_ftcontb_amount(self):
    #     for partner in self:
    #         payment = partner.payment_ids.sudo().sorted(lambda p: p.date or p.create_date)[:1]
    #         partner.ftcontb = int(payment.amount) if payment else 0

    # Printing Label for single contact
    def print_khabarname_label(self):
        self.ensure_one()
        return self.env.ref('visio_contact_extension_qa.action_report_khabarname_label').report_action(self)

    whatsapp_status_qa = fields.Char(string="WhatsApp Status")
    ref_mobile_qa = fields.Char(string="Ref. Mobile")
