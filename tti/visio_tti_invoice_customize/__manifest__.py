# -*- coding: utf-8 -*-
{
    'name': "Tti Invoice Customizations",
    'summary': "Tti Invoice Customizations",
    'description': """Tti Invoice Customizations""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Accounting',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -200,

    'depends': ['base', 'sale', 'sale_management', 'sales_team', 'visio_tti_so_customize', 'account', 'purchase' , 'accountant'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/account_multi_payments.xml',
        'views/account_payment_register.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/account_payment.xml',
        # 'report/multi_payments.xml',
    ],
    'demo': [],

    'images': [],
    'application': True,
    'installable': True,
    'auto_install': False,
}

