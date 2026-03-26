# -*- coding: utf-8 -*-

{
    'name': "Email Templates",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'mail', 'visio_cit_sale_customization'],

    # always loaded
    'data': [
        'data/email_template_existing_customer.xml',
        # 'data/email_template_new_customer.xml',
    ],

}
