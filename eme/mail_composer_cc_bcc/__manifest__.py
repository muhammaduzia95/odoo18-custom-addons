# -*- coding: utf-8 -*-
{
    'name': "mail_composer_cc_bcc",

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
       "depends": [
        "mail",
    ],
    "data": [
        "views/res_company_views.xml",
        "views/mail_mail_views.xml",
        "views/mail_message_views.xml",
        "views/mail_template_views.xml",
        "wizards/mail_compose_message_view.xml",
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

