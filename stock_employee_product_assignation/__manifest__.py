# -*- coding: utf-8 -*-
{
    'name': "Stock Product Assignation for Employees",
    'summary': """
        Stock Product Assignation for Employees
    """,
    'description': """
        Stock Product Assignation for Employees
    """,
    # 'author': "Ingetive",
    # 'website': "https://ingetive.com",
    'category': 'Stock',
    'version': '13.0.1.0.1',
    'depends': [
        'stock',
        'project',
        'tetrace'
    ],
    'data': [
        # Security
        # 'security/product_assignation_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/stock_location_data.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',

        # Report
        'reports/stock_employee_product_assignation_report.xml',

        # Views
        'views/product_assignation_views.xml',
        'views/project_views.xml',
        'views/product_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',

        # Wizard
        # 'wizards/.xml',
    ],
    'qweb': [
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}