# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>
{
    'name': "Tetrace",
    'summary': """""",
    'description': """""",
    'author': "Ingetive",
    'website': "http://ingetive.com",
    'category': 'Uncategorized',
    'version': '13.0.1.0.1',
    'depends': [
        'base',
        'account',
        'account_reports',
        'l10n_ar',
        'l10n_latam_invoice_document'
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/account.xml',
        'report/web.xml',
        'views/account_financial_report.xml',
        'views/account_move_line.xml',
        'views/account_account.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
