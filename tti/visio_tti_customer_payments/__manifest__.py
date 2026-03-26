# -*- coding: utf-8 -*-
{
    'name': "Tti Customer Payments",
    'summary': "Tti Customer Payments",
    'description': """Tti Customer Payments""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Accounting',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -250,

    'depends': ['base', 'account', 'accountant'],
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/account_payment.xml',
        'views/receipt_voucher_report.xml'
    ],
    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

