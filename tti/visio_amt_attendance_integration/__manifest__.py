# -*- coding: utf-8 -*-
{
    'name': "Tti AMT Device Attendance Integration",
    'summary': "Tti AMT Device Attendance Integration",
    'description': """Tti AMT Device Attendance Integration""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Human Resources',
    'license': 'LGPL-3',
    'version': '1.0',
    'sequence': -100,

    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/device_attendance_views.xml',
        'views/menu.xml',
    ],
    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

