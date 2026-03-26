# -*- coding: utf-8 -*-
{
    'name': "Tti Exel Reports",
    'summary': "Tti Exel Reports",
    'description': """Tti Exel Reports""",

    'author': "Visiomate",
    'company': 'Visiomate',
    'maintainer': 'Visiomate',
    'website': "https://www.visiomate.com",

    'category': 'Sales', 
    'license': 'LGPL-3',
    'version': '1.0.1',
    'sequence': -250,

    'depends': ['base', 'hr', 'visio_tti_so_customize', 'sale', 'sale_management', 'sales_team', 'product', 'purchase',
                'account', 'purchase', 'crm', 'visio_tti_invoice_customize' , 'visio_tti_customer_payments' ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_account.xml',

        'report/party_ledger_report_pdf.xml',
        'report/party_receivable_report_pdf.xml',
        'report/report_action.xml',
        'report/sales_tax_report_pdf.xml',

        'wizard/eurofins_sales_report.xml',
        'wizard/recovery_report.xml',
        'wizard/sales_tax_report.xml',
        'wizard/tti_reports_wizard.xml',
    ],
    'demo': [],

    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}
