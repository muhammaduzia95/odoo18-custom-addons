# -*- coding: utf-8 -*-
{
    'name': "visio_tti_timeoff_portal",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base' , 'web' , 'website' , 'hr_holidays' , 'portal' , 'website_hr_recruitment', 'visio_tti_hr_customize'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'views/timeoff_template.xml',
        'views/timeoff_form.xml',
        'views/timeoff_view.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'visio_tti_timeoff_portal/static/src/css/timeoff_portal.css',
            'visio_tti_timeoff_portal/static/src/js/timeoff_attachments.js',
        ],
    },

    # only loaded in demonstration mode
    'demo': [
    ],
}

