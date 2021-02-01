# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>
{
    'name': "Horas Dashboard",
    'summary': """""",
    'description': """""",
    'author': "Ingetive",
    'website': "https://ingetive.com",
    'category': 'Uncategorized',
    'version': '13.0.1.0.1',
    'depends': [
        'base',
        'base_setup'
    ],
    'data': [
        'views/assets.xml',
        # 'views/res_config_settings.xml',
    ],
    'qweb': [
        "static/src/xml/web_world_clock.xml",
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
