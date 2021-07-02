# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, modules

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = "res.users"

    validacion_user_ids = fields.One2many('tetrace.validacion_user', 'user_id')
    rango_validaciones = fields.Integer("Rango", default= 6)
    sale_order_coordinador_ids = fields.One2many("sale.order", "coordinador_proyecto_id")
    warehouse_ids = fields.One2many('stock.warehouse', 'responsable_exportacion_id')
    employee_ids = fields.Many2many("hr.employee", string="Empleados", compute="_compute_employee_ids")
    
    def _compute_employee_ids(self):
        for r in self:
            employees = self.env['hr.employee'].sudo().search([('user_id', '=', r.id)])
            r.employee_ids = [(6, 0, employees.ids)]
    