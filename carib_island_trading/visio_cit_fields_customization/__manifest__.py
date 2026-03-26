# -*- coding: utf-8 -*-
{
    'name': "Fields Customization",

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
    'depends': ['base', 'product', 'sale', 'account', 'purchase', 'visio_cit_purchase_request',
                'visio_cit_sale_customization', 'stock', 'purchase_stock',
                'sale_management', 'analytic'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/group.xml',
        'report/delivery_report_view.xml',
        'report/invoice_report_view.xml',
        'report/purchase_order_report.xml',
        'report/sale_order_report_view.xml',

        'views/account_move_line_view.xml',
        'views/product_view.xml',
        'views/purchase_order_line_view.xml',
        'views/purchase_request_view.xml',
        'views/sale_order_line_view.xml',


    ],

}

