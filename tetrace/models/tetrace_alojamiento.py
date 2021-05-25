# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
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
    observaciones = fields.Text("Observaciones", translate=True)
    task_id = fields.Many2one("project.task", string="Tarea")
    
    @api.constrains("fecha", "fecha_fin")
    def _check_fechas(self):
        for r in self:
            if r.fecha and r.fecha_fin and r.fecha > r.fecha_fin:
                raise ValidationError(_("La fecha fin tiene que se superior a la de entrada"))