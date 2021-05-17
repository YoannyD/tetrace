# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Asignacion(models.Model):
    _name = "tetrace.asignacion"
    _description = "Asignaciones"
    
    company_id = fields.Many2one("res.company", string="Compañia", required=True)
    task_id = fields.Many2one('project.task', string="Tarea", required=True,
                              domain="[('project_id.sale_order_id', '=', False)]")
    responsable_id = fields.Many2one('res.users', string="Responsable")
    seguidor_ids = fields.Many2many('res.users', string="Seguidor")