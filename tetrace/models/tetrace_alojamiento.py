# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Alojamiento(models.Model):
    _name = "tetrace.alojamiento"
    _description = "Alojamientos"
    
    fecha = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")
    ciudad = fields.Char("Ciudad", translate=True)
    completado = fields.Boolean("Completado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    employee_active_ids = fields.Many2many("hr.employee", related="task_id.project_id.tecnico_ids")
    observaciones = fields.Text("Observaciones", translate=True)
    task_id = fields.Many2one("project.task", string="Tarea")
    
    @api.model
    def create(self, vals):
        res = super(Alojamiento, self).create(vals)
        res.create_task_activity("create")
        return res
    
    def write(self, vals):
        res = super(Alojamiento, self).write(vals)
        self.create_task_activity("update")
        return res
    
    def create_task_activity(self, accion):
        for r in self:
            if not r.task_id or (accion == "update" and r.realizado):
                continue
            
            sumanry = None
            if accion == "create":
                summary = _('Gestionar alojamiento para %s del proyecto %s' % (r.employee_id.name, r.task_id.project_id.name))
            elif accion == "update":
                summary = _('Gestionar modificación alojamiento para %s del proyecto %s' % (r.employee_id.name, r.task_id.project_id.name))
            
            fecha = r.fecha - timedelta(days=5) if r.fecha else None
            self.task_id.create_activity(summary, fecha)
    
    @api.constrains("fecha", "fecha_fin")
    def _check_fechas(self):
        for r in self:
            if r.fecha and r.fecha_fin and r.fecha > r.fecha_fin:
                raise ValidationError(_("La fecha fin tiene que se superior a la de entrada"))