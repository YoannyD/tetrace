# -*- coding: utf-8 -*-
{
    'name': "World Clock",

    'summary': 'Shows clock according to timezone',

    'description': """
        Shows clock according to timezone
    """,

    'author': "Deligence",
    'website': "https://deligence.com",
    'category': 'Tools',
    'version': '1.0',
    'license': 'LGPL-3',
    'images': ['static/description/main_screenshot.png', 'static/description/main_1.png', 'static/description/main_2.png', 'static/description/main_3.png', 'static/description/main_4.png'],

    # any module necessary for this one to work correctly
    'depends': ['base', 'website'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/snippets.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
