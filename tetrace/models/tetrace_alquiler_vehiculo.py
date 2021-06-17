# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta

_logger = logging.getLogger(__name__)


class AlquilerVehiculo(models.Model):
    _name = "tetrace.alquiler_vehiculo"
    _description = "Alquileres vehículos"
    
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")
    recogida = fields.Text("Recogida", translate=True)
    entrega = fields.Text("Entrega", translate=True)
    completado = fields.Boolean("Completado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    observaciones = fields.Text("Observaciones", translate=True)
    task_id = fields.Many2one("project.task", string="Tarea")
    
    @api.model
    def create(self, vals):
        res = super(AlquilerVehiculo, self).create(vals)
        res.create_task_activity("create")
        return res
    
    def write(self, vals):
        res = super(AlquilerVehiculo, self).write(vals)
        res.create_task_activity("update")
        return res
    
    def create_task_activity(self, accion):
        for r in self:
            if not r.task_id or (accion == "update" and r.realizado):
                continue
            
            sumanry = None
            if accion == "create":
                summary = _('Gestionar alquiler de vehículo del proyecto %s' % r.task_id.project_id.name)
            elif accion == "update":
                summary = _('Gestionar modificación alquiler de vehículo del proyecto %s' % r.task_id.project_id.name)
                
            fecha = r.fecha_inicio - timedelta(days=5) if r.fecha_inicio else None
            self.task_id.create_activity(summary, fecha)
    
    