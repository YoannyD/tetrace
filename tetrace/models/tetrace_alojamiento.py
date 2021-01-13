# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Alojamiento(models.Model):
    _name = "tetrace.alojamiento"
    _description = "Alojamientos"
    
    fecha = fields.Date("Fecha")
    ciudad = fields.Char("Ciudad", translate=True)
    completado = fields.Boolean("Completado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    observaciones = fields.Text("Observaciones", translate=True)
    task_id = fields.Many2one("project.task", string="Tarea")