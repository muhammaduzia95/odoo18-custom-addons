# -*- coding: utf-8 -*-
{
    'name': "EME pdf Templates",

    'summary': 'Custom PDF layout for Purchase, Sales, Invoice',

    'description': """
    This module provides a customized PDF invoice report 
    for the Accounting app in Odoo 18.
    """,

    'author': "Visiomate - Zia",
    'website': "https://www.visiomate.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'account', 'sale', 'product', 'purchase', 'cloudmen_eme_quotation'],

    # always loaded
    'data': [

        # Report
        'report/cover.xml',
        'report/custom_footer.xml',
        'report/custom_header.xml',
        'report/eme_delivery_note_pdf.xml',
        'report/eme_goods_receipt_pdf.xml',
        'report/eme_material_issue_note_pdf.xml',
        'report/eme_material_request_pdf.xml',
        'report/eme_material_return_note.xml',
        'report/eme_proforma_service_pdf.xml',
        'report/eme_purchase_order_pdf.xml',
        'report/eme_quotation_pdf.xml',
        'report/eme_rfq_pdf.xml',
        'report/eme_supplier_invoice_pdf.xml',
        'report/eme_tax_credit_note_pdf.xml',
        'report/eme_tax_debit_note_pdf.xml',
        'report/eme_tax_invoice_pdf.xml',

        # View
        'views/account_move_view.xml',
        'views/hide_reports_menus.xml',
        'views/product_template_view.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',

    ],

}
