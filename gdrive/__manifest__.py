# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>
{
    'name': "Google Drive Ingetive",
    'summary': """""",
    'author': "Ingetive",
    'website': "http://ingetive.com",
    'category': 'Uncategorized',
    'version': '13.0.1.0.1',
    'depends': [
        'base_setup',
        'base',
        'website',
        'google_account'
    ],
    'data': [
        # 'data/mails.xml',
        'views/res_users.xml',
        'views/res_config_settings.xml',
        'templates/google_drive.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
