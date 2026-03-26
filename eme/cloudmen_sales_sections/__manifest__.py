# -*- coding: utf-8 -*-
{
      'name': "Cloudmen Sales Sections",
    'summary': "Enhancements for Sale Order report including section-wise total quantities and pricing.",
    'description': """
This module enhances the Sale Order report by adding the functionality to display total quantities and prices for each section. It also provides an option to hide or display pricing information in the report, depending on the user's preference.
    """,
    'author': "",
    'website': "https://www.yourcompany.com",

    'author': "Cloudmen",
    'website': "https://www.cloudmen.ae/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','mail','sale_pdf_quote_builder','crm','crm_sms'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        # 'views/sale_report_inherit.xml', #zia comment
        'views/stages_view.xml',
        'views/sale_custom_report.xml',
        'views/crm_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

