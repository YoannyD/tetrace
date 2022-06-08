# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    employees = env['hr.employee'].search([])
    companies = env['res.company'].with_context(active_test=False).search([])
    for employee in employees:
        for company in companies:
            employee.with_context(company_id=company.id, default_company_id=company.id, force_company=company.id).write({'codigo_trabajador_company': employee.codigo_trabajador_A3})
    a = 1


