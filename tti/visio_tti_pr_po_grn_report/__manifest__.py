# -*- coding: utf-8 -*-
{
    'name': "Tti PR PO GRN Reports",
    'summary': "Tti PR PO GRN Reports",
    'description': """Tti PR PO GRN Reports""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Purchase',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -250,

    'depends': ['base' , 'purchase', 'visio_tti_po_customize'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_order_report.xml',
        'views/grn_report.xml',
        'views/igp_report.xml',
        'views/gin_report.xml',
        'views/sin_report.xml',
        'views/stock_picking.xml',
    ],

    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

