# -*- coding: utf-8 -*-
{
    'name': "Tti Parcel Inherit",
    'summary': "Tti Parcel Inherit",
    'description': """Tti Parcel Inherit""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Sales',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -250,

    'depends': ['base', 'sale', 'sale_management', 'sales_team', 'visio_tti_so_customize'],
    'data': [
        'security/ir.model.access.csv',
        'views/tti_parcels.xml',
    ],
    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

