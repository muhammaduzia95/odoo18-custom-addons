# -*- coding: utf-8 -*-
{
    'name': "Copy Order Line",

    'summary': """
        copy order line""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Youssef Mohamed",
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'module_type': 'official',
    # any module necessary for this one to work correctly
    'depends': ['base','sale','sale_renting','account'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'copy_order_line/static/src/js/section_and_note_fields_backend.js',
            'copy_order_line/static/src/xml/section_and_note_fields_backend.xml',
        ],
    },

}
