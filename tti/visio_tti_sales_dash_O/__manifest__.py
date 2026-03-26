# -*- coding: utf-8 -*-
{
    'name': "TTi Sales Dashboard",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
    Long description of module's purpose
    """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Dashboard',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account', 'web', 'visio_tti_so_customize', 'spreadsheet_dashboard'],

    # always loaded
    'data': [
        'views/inherit_target_achieve.xml',
        'views/tti_sales_dashboard_menu.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'visio_tti_sales_dash/static/src/xml/tti_dashboard_templates.xml',
            'visio_tti_sales_dash/static/src/js/tti_dashboard.js',
            # 'visio_tti_sales_dash/static/src/css/tti_dashboard.css',
        ],
        'web.assets_backend_lazy': [
            'visio_tti_sales_dash/static/src/js/tti_dashboard.js',
        ],
        "web.assets_common": [
            'visio_tti_sales_dash/static/src/css/tti_dashboard.css',
        ],
    },
}
