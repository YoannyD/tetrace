# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

TIPOS_AUSENCIAS = [
    ('rotacion', _("Rotación")),
    ('formacion', _("Formación")),
    ('permiso', _("Permiso")),
]


class Ausencia(models.Model):
    _name = "tetrace.ausencia"
    _description = "Ausencias"
    
    task_id = fields.Many2one('project.task', string="Tarea")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    ausencia = fields.Selection(TIPOS_AUSENCIAS, string="Tipo ausencia")
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")
    realizado = fields.Boolean("Realizado")
    
    @api.model
    def create(self, vals):
        res = super(Ausencia, self).create(vals)
        res.create_task_activity("create")
        return res
    
    def write(self, vals):
        res = super(Ausencia, self).write(vals)
        res.create_task_activity("update")
        return res
    
    def create_task_activity(self, accion):
        for r in self:
            if not r.task_id and r.realizado:
                continue
            
            sumanry = None
            if accion == "create":
                summary = _('Gestionar ausencia del proyecto %s' % r.task_id.project_id.name)
            elif accion == "update":
                summary = _('Gestionar modificación ausencia del proyecto %s' % r.task_id.project_id.name)
                
            fecha = r.fecha_inicio - timedelta(days=5) if r.fecha_inicio else None
            self.task_id.create_activity(summary, fecha)