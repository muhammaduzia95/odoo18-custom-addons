# -*- coding: utf-8 -*-
{
    'name': "Tti Users Customizations",
    'summary': "Tti Users Customizations",
    'description': """Tti Users Customizations""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Sales',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -280,

    'depends': ['base', 'sale', 'sale_management', 'sales_team', 'product', 'purchase', 'visio_tti_so_customize'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_users.xml',
    ],
    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}