# -*- coding: utf-8 -*-
{
    'name': "Contact Extension",

    'summary': "Adds custom fields, transaction wizards, label printing, and election management features to the Contacts module.",

    'author': "Visiomate",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Contact',
    'version': '0.8',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'hr', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',

        'data/partner_sequence.xml',

        'wizard/create_transaction_wizard_view.xml',
        'wizard/monthly_due_pdf_wizard_view.xml',
        'wizard/elections_wizard_view.xml',
        'wizard/lables_list_wizard_view.xml',

        'views/account_payment_view.xml',
        'views/res_partner_view.xml',

        'views/list_by_hand.xml',
        'views/list_election_candidates.xml',
        'views/list_election_voters.xml',

        'views/labels_election_candidates.xml',
        'views/labels_election_voter.xml',
        'views/lable_khabarname.xml',
        'views/lables_mohsineen.xml',

        'views/report_monthly_due.xml',
        'views/receipt_partner.xml',

        'views/menus.xml',
    ]

}
