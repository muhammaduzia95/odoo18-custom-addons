from odoo import models, fields , api , _

class Employee(models.Model):
    _inherit = 'hr.employee'

    father_name = fields.Char(string='Father Name')
    blood_group = fields.Char(string='Blood Group')
    eobi_number = fields.Char(string='EOBI Number')

    # Probation Checklist
    confirmation_letter = fields.Boolean(string="Confirmation letter system based")
    paid_leaves = fields.Boolean(string="Paid leaves")
    health_insurance = fields.Boolean(string="Health Insurance")
    salary_change = fields.Boolean(string="Salary Change")
    probation_extension = fields.Boolean(string="Probation Extension")

    # Onboarding Checklist
    email_to_it = fields.Boolean(string="Email to IT for new hiring setup")
    induction_documents = fields.Boolean(string="Induction Documents (attached)")
    photograph = fields.Boolean(string="Photograph")
    cnic = fields.Boolean(string="CNIC")
    testimonials = fields.Boolean(string="Testimonials")
    orientation_plan = fields.Boolean(string="Orientation plan")
    training_plan = fields.Boolean(string="Training plan (if applicable)")
    jds_handover = fields.Boolean(string="JDs to be handed over")
    sim = fields.Boolean(string="Sim")
    visiting_cards = fields.Boolean(string="Visiting Cards (If required)")
    salary_account_requirements = fields.Boolean(string="Requirements for salary accounts")

    # Offboarding Checklist
    resignation_letter = fields.Boolean(string="Hand written resignation with impression")
    handing_over_doc = fields.Boolean(string="Handing over document")
    return_items = fields.Boolean(string="Return of all issued items on D.O.L.")
    insurance_removal = fields.Boolean(string="Health insurance removal on D.O.L.")
    clearance_certificate = fields.Boolean(string="Clearance Certificate signed")
    notice_period_status = fields.Boolean(string="Notice period status")
    final_settlement = fields.Boolean(string="Final Settlement of account")
    signoff_declaration = fields.Boolean(string="Signing off Declaration & Cheque handover")

    @api.model
    def create_portal_users_for_employees(self):
        """Create portal users for employees with menu access rights"""
        employees = self.search([('user_id', '=', False), ('barcode', '!=', False), ('active', '=', True)])

        portal_group = self.env.ref('base.group_portal')

        custom_group = self.env['res.groups'].sudo().search([
            ('name', '=', 'Employee Portal Users_2'),
            ('category_id', '=', self.env.ref('base.module_category_human_resources').id)
        ], limit=1)

        if not custom_group:
            custom_group = self.env['res.groups'].sudo().create({
                'name': 'Employee Portal Users_2',
                'category_id': self.env.ref('base.module_category_human_resources').id,
                'implied_ids': [(4, portal_group.id)],
            })

        menu_model = self.env['ir.model'].sudo().search([('model', '=', 'ir.ui.menu')], limit=1)
        existing_menu_access = self.env['ir.model.access'].sudo().search([
            ('model_id', '=', menu_model.id),
            ('group_id', '=', custom_group.id)
        ], limit=1)

        if not existing_menu_access:
            self.env['ir.model.access'].sudo().create({
                'name': 'Portal Menu Access',
                'model_id': menu_model.id,
                'group_id': custom_group.id,
                'perm_read': True,
                'perm_write': False,
                'perm_create': False,
                'perm_unlink': False,
            })

        activity_model = self.env['ir.model'].sudo().search([('model', '=', 'mail.activity.type')], limit=1)
        existing_activity_access = self.env['ir.model.access'].sudo().search([
            ('model_id', '=', activity_model.id),
            ('group_id', '=', custom_group.id)
        ], limit=1)

        if not existing_activity_access:
            self.env['ir.model.access'].sudo().create({
                'name': 'Activity Type Read Access for Portal Users',
                'model_id': activity_model.id,
                'group_id': custom_group.id,
                'perm_read': True,
                'perm_write': False,
                'perm_create': False,
                'perm_unlink': False,
            })

        for employee in employees:
            user = self.env['res.users'].sudo().create({
                'name': employee.name,
                'login': employee.barcode,
                'email': employee.email or '',
                'password': employee.barcode,
                'groups_id': [(6, 0, [custom_group.id])],
                'share': True,  # Mark as portal user
            })
            employee.user_id = user.id


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'


    father_name = fields.Char(related='employee_id.father_name', readonly=True)
    blood_group = fields.Char(related='employee_id.blood_group', readonly=True)
    eobi_number = fields.Char(related='employee_id.eobi_number', readonly=True)

    # @api.model
    # def create_portal_users_for_employees(self):
    #     """Create portal users for employees who don't have a user_id"""
    #     employees = self.search([('user_id', '=', False), ('barcode', '!=', False)])
    #
    #     portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
    #
    #     for employee in employees:
    #         user = self.env['res.users'].create({
    #             'name': employee.name,
    #             'login': employee.barcode,
    #             'email': employee.barcode,
    #             'password': employee.barcode,
    #             'groups_id': [(6, 0, [portal_group.id])] if portal_group else False,
    #         })
    #         employee.user_id = user.id
