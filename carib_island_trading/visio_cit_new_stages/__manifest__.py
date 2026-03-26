{
    'name': "visio_cit_new_stages",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
    Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','sale','purchase','sale_management', 'visio_cit_sale_purchase'],

    'data': [
        'security/ir.model.access.csv',
        'views/sale_stages.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/purchase_stages.xml',
    ],
    'demo': [],
}