# -*- coding: utf-8 -*-
{
    'name': "Payment Recovery Report",

    # 'summary': "Short (1 phrase/line) summary of the module's purpose",

    # 'description': """
    # Long description of module's purpose
    #     """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'visio_tti_customer_payments', 'visio_tti_exel_reports'],

    # always loaded
    'data': [

        'security/ir.model.access.csv',             # wiz security
        'security/payment_recovery_security.xml',   # group
        'report/payment_recovery_pdf.xml',          # report
        'views/account_payment_register_view.xml',  # customization
        'views/account_payment_view.xml',           # customization
        'wizard/payment_recovery_wizard_view.xml',  # report/wizard

    ],

}
