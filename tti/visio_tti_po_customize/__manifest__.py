# -*- coding: utf-8 -*-
{
    'name': "Tti Purchase Order Customizations",
    'summary': "Tti Purchase Order Customizations",
    'description': """Tti Purchase Order Customizations""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Purchase',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -250,

    'depends': ['base' , 'purchase' , 'stock'],

    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
        'views/po_project_tags.xml',
    ],
    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

