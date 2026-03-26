# -*- coding: utf-8 -*-
{
    'name': "Attendance Portal",

    'summary': "Added Missed Attendance feature for employees, "
               "and a Marketing Attendance Portal for marketing employees",

    # 'description': """
    # Long description of module's purpose
    #     """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_attendance', 'portal', 'mail', 'visio_tti_hr_customize'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/attendance_portal_rules.xml',

        'views/res_users_view.xml',
        'views/tti_hr_attendance_approval_view.xml',

        'views/tti_attendance_portal_view.xml',

        'views/missed_atten_portal_templates.xml',
        'views/marketing_atten_portal_templates.xml',
        'views/manager_approval_portal_templates.xml',

    ],

}
