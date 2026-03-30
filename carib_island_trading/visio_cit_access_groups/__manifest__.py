# -*- coding: utf-8 -*-
{
    'name': "Access Groups",

    'summary': "Access groups for sales team -> Accounting/Customer and purchase team -> Accounting/Vendor, ",

    # 'description': """
    # Long description of module's purpose
    #     """,

    'author': "Visiomate -Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    # 'category': 'Sales, Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'purchase'],

    # always loaded
    'data': [
        'security/group.xml',
        'views/view_sales_menus.xml',
    ],

}

