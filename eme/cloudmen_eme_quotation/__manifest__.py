# -*- coding: utf-8 -*-
{
    'name': "cloudmen_eme_quotation",

    'summary': "new customize quotation for sales",

    'description': """
Long description of module's purpose
    """,

    'author': "Cloudmen",
    'website': "https://www.cloudmen.ae",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '17.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_crm'],

    # always loaded
    'data': [
        'views/sale_order.xml',
    ],

}
