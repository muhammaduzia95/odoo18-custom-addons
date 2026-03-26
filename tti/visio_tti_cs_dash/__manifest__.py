# -*- coding: utf-8 -*-
{
    'name': "CS Dashboard",

    # 'summary': "Short (1 phrase/line) summary of the module's purpose",
    # 'description': """
    # Long description of module's purpose
    #     """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Dashboard',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'spreadsheet_dashboard', 'web', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/tti_cs_dashboard_menu.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'web/static/lib/Chart/Chart.js',
            'visio_tti_cs_dash/static/src/xml/cs_dashboard_view.xml',
            'visio_tti_cs_dash/static/src/js/cs_dashboard.js',
            # 'visio_tti_cs_dash/static/src/css/cs_dashboard.css',
        ],
        'web.assets_backend_lazy': [
            'visio_tti_cs_dash/static/src/js/cs_dashboard.js',
        ],
        "web.assets_common": [
            # 'visio_tti_cs_dash/static/src/css/cs_dashboard.css',
        ],
    },
}
