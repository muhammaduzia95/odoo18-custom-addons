# -*- coding: utf-8 -*-
{
    'name': "Tti HR Customizations",
    'summary': "Tti HR Customizations",
    'description': """Tti HR Customizations""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Hr',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -200,

    'depends': ['base', 'hr', 'hr_contract', 'hr_payroll', 'hr_work_entry_contract_enterprise', 'hr_attendance',
                'hr_holidays','account' , 'hr_payroll_account' , 'analytic'],
    'data': [
        # 'security/ir.model.access.csv',
        'security/groups.xml',
        'data/cron.xml',
        'views/hr_employee.xml',
        'views/hr_contract.xml',
        # Remove the old inheritance file
        # 'views/payroll_dashboard_inherit.xml',
    ],
    'demo': [],

    'assets': {
        'web.assets_backend': [
            'visio_tti_hr_customize/static/src/xml/payroll_checklist.xml',
            'visio_tti_hr_customize/static/src/xml/payroll_dashboard_inherit.xml',  # Add the new template
            'visio_tti_hr_customize/static/src/js/payroll_checklist.js',
            'visio_tti_hr_customize/static/src/js/payroll_dashboard.js',
        ],
    },

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}
