{
    'name': "Purchase Order Report",
    'author': 'Cloudmen',
    'website': 'http://cloudmen.ae',
    'summary': """""",
    'category': 'Uncategorized',
    'version': '17.1',
    'depends': ['base', 'purchase', 'project','product'],
    'data': [
        'views/res_company_view.xml',
        'views/product.xml',
        'views/product_template.xml',
        'report/header_footer.xml',
        'report/purchase_order_report.xml',
        'views/purchase_order.xml',
        'report/reports.xml',

    ],
}
