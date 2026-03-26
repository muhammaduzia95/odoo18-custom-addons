{
    'name': 'EKTEFA HRMS - اكتفاء نظام الموارد البشرية',
    'version': '1.0',
    'sequence': 18,
    'summary': 'EKTEFA HRMS - اكتفاء نظام الموارد البشرية',
    'description': """
        This app integrates Odoo with Ektefa Payroll System for seamless payroll management.

        For more information, visit: https://www.ektefa.net

        Developer contact and more details: https://www.beviable.com
    """,
    'category': 'Accounting',
    'author': 'Ektefa',
    'maintainer': 'Ektefa',
    'company': 'Ektefa',
    'website': 'https://www.ektefa.net',
    'support': 'https://www.beviable.com',
    'license': 'LGPL-3',
    'depends': ['base', 'l10n_sa', 'account'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/payrun_views.xml',
        'views/end_of_service_views.xml',
        'views/loan_views.xml',
        'views/loan_settlement_views.xml',
        'views/api_log_views.xml',
        'views/config_settings_views.xml',
        'views/account_move_views.xml',
        'data/ektefa_menu.xml',
        'data/cron_data.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
