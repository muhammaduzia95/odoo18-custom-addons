# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_atten_leave_policy\__manifest__.py
# -*- coding: utf-8 -*-
{
    'name': "Attendance | Leave Policy",

    'summary': "Automated handling of late clock-ins, single clocks, and overtime comp-off policies.",

    'description': """
    Implements attendance and leave policies for TTI:
    - Late clock-ins (warnings, leave & salary deduction)
    - Single clock handling (auto completion, tagging, deduction)
    - Overtime tracking (comp-off generation, HR approval)
    """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_attendance', 'hr_holidays'],

    # always loaded
    'data': [
        # security
        # 'security/ir.model.access.csv',

        # views
        # 'views/late_clockin_views.xml',
        # 'views/single_clock_views.xml',
        # 'views/overtime_policy_views.xml',

        # cron jobs (optional)
        # 'data/cron_jobs.xml',
    ],

}
