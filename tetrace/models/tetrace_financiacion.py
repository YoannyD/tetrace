# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Financiacion(models.Model):
    _name = "tetrace.financiacion"
    _description = "Financiaciones"
    
    task_id = fields.Many2one('project.task', string="Tarea")
    employee_id = fields.Many2one('hr.employee', string="Persona")
    importe = fields.Monetary('Importe')
    currency_id = fields.Many2one("res.currency", related="task_id.currency_id")
    fecha = fields.Date('Fecha')
    realizado = fields.Boolean('Realizado')