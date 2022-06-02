# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class FixDatabase(models.TransientModel):
    _name = 'fix.database'

    action = fields.Selection([
        ('update_code_company', 'Update Code Company'),
    ], 'Action', required=True)

    def execute_action(self):
        result = getattr(self, self.action)()
        return {'type': 'ir.actions.act_window_close'}

    def update_code_company(self):
        employees = self.env['hr.employee'].search([])
        companies = self.env['res.company'].with_context(active_test=False).search([])
        for employee in employees:
            for company in companies:
                if employee.company_id.id == company.id:
                    employee.with_context(company_id=company.id, default_company_id=company.id,
                                          force_company=company.id).write(
                        {'codigo_trabajador_company': employee.codigo_trabajador_A3})
                    _logger.warning("Actualizado correctamente, valor para compania")
                else:
                    employee.with_context(company_id=company.id, default_company_id=company.id,
                                          force_company=company.id).write(
                        {'codigo_trabajador_company': ''})
                    _logger.warning("Actualizado correctamente, sin valor")
