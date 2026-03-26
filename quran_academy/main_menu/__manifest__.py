{
    "name": "Main Menu",
    "version": "1.1.0",
    "summary": "Enhanced navigation module for Odoo Community Edition.",
    "description": """
        This module provides a centralized main menu for Odoo Community Edition, allowing users to quickly access core modules and enhance their workflow. 
        It features widget functionality for displaying the current date and posting announcements, which can be managed by administrators. 
        Users can create bookmarks for quick access to essential menus, as well as external links, improving overall navigation efficiency.
    """,
    'sequence': -100,
    "author": "Axel Manzanilla",
    "maintainer": "Axel Manzanilla",
    "website": "https://axelmanzanilla.com",
    "license": "LGPL-3",
    "category": "Technical/Technical",
    "depends": [
        "base",
        "web",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        'views/web_login.xml',
        # 'views/messaging_menu.xml',
        "views/main_menu_views.xml",
        "views/menu_bookmark_views.xml",
        "views/res_config_setting_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "main_menu/static/src/components/**/*",
            "main_menu/static/src/js/ExtendedUserMenu.js",
        ],
    },

    "images": [
        "static/description/banner.png",
    ],
    "auto_install": True,
    "application": True,
    "installable": True,
}
