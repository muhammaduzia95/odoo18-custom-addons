# -*- coding: utf-8 -*-
{
    'name': "TTI Reporting",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
    Long description of module's purpose
    """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Reporting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account', 'visio_tti_so_customize'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/levis_report_view.xml',
        'views/menu.xml',
        'wizard/daily_ledger_wizard_view.xml',
        'wizard/daily_summary_wizard_view.xml',
        'wizard/invoice_daily_summary_wizard_view.xml',
    ],

}

