# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>
{
    'name': "Registro tiempos",
    'summary': """""",
    'description': """""",
    'author': "Ingetive",
    'website': "https://ingetive.com",
    'category': 'Uncategorized',
    'version': '13.0.1.0.1',
    'depends': [
        'base',
        'portal',
        'project',
        'hr_attendance',
        'tetrace'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/registro_tiempo_tiempo.xml',
        'views/project_project.xml',
        'views/project_task.xml',
        'views/hr_attendance.xml',
        'templates/assets.xml',
        'templates/registro_tiempo.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
