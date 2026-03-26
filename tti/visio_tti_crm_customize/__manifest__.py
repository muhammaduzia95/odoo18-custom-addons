# -*- coding: utf-8 -*-
{
    'name': "Tti CRM Customizations",
    'summary': "Tti CRM Customizations",
    'description': """Tti CRM Customizations""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Sales',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -200,

    'depends': ['base', 'crm',],
    'data': [
        # 'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
    ],
    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

