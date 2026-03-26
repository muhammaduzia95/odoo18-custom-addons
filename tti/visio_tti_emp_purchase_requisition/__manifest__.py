# -*- coding: utf-8 -*-
{
    'name': "Tti PO Purchase Requisition",
    'summary': "Tti PO Purchase Requisition",
    'description': """Tti PO Purchase Requisition""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Purchases',
    'license': 'LGPL-3',
    'version': '18.0.1.0.0',
    'sequence': -200,

    'depends': ['base', 'hr', 'stock', 'purchase', 'visio_tti_so_customize',],
    'data': [
        'security/employee_purchase_requisition_groups.xml',
        'security/employee_purchase_requisition_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/pr_report.xml',
        'views/employee_purchase_requisition_views.xml',
        'views/requisition_order_views.xml',
        'views/employee_purchase_requisition_menu.xml',
        'views/purchase_order_views.xml',
    ],
    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

