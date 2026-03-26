# -*- coding: utf-8 -*-
{
    'name': "Sale Customization",

    # 'summary': "Short (1 phrase/line) summary of the module's purpose",

    # 'description': """
    # Long description of module's purpose
    #     """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_management', 'purchase', 'visio_cit_purchase_request', 'stock', 'sale_stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/product_pricelist_rules.xml',
        'data/res_partner_rules.xml',

        'views/account_move_view.xml',
        'views/product_pricelist_view.xml',
        'views/res_partner_view.xml',
        'views/res_users_view.xml',
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
    ],

}
