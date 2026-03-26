# -*- coding: utf-8 -*-
{
    'name': "Sales: Margin & Markup",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
            Long description of module's purpose
    """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'visio_cit_sale_customization'],

    # always loaded
    'data': [
        'views/inherit_sale_order.xml',
    ],
}

