# -*- coding: utf-8 -*-
{
    'name': "Missed Attendance",

    # 'summary': "Short (1 phrase/line) summary of the module's purpose",

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
    'depends': ['base', 'hr', 'hr_attendance', 'portal', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/missed_attendance_views.xml',
        'views/portal_templates.xml',

    ],
}

