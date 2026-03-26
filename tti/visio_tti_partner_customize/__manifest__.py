# -*- coding: utf-8 -*-
{
    'name': "Tti Partner Customizations",
    'summary': "Tti Partner Customizations",
    'description': """Tti Partner Customizations""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Contact',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -200,

    'depends': ['base', 'sale', 'sale_management', 'sales_team', 'product', 'purchase', 'account', 'purchase' , 'accountant',
                'contacts' , 'visio_tti_so_customize' , 'hr_appraisal'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/res_company.xml',
    ],
    'demo': [],

    'images': [],
    'application': True,
    'installable': True,
    'auto_install': False,
}

