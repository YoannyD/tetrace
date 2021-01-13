# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AlquilerVehiculo(models.Model):
    _name = "tetrace.alquiler_vehiculo"
    _description = "Alquileres vehículos"
    
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")
    recogida = fields.Text("Recogida")
    entrega = fields.Text("Entrega")
    completado = fields.Boolean("Completado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    observaciones = fields.Text("Observaciones")
    task_id = fields.Many2one("project.task", string="Tarea")
    
    