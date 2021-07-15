# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TecnicoCalendario(models.Model):
    _name = 'tetrace.tecnico_calendario'
    _description = "Técnicos calendarios"
    
    project_id = fields.Many2one('project.project', string="Proyecto", required=True)
    employee_id = fields.Many2one('hr.employee', string="Técnico", required=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string="Calendario", required=True)
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    rating = fields.Char("Evaluación")
    observaciones = fields.Text("Observaciones")
    
    @api.constrains("fecha_inicio", "fecha_fin")	
    def _check_fechas(self):
        for r in self:
            if r.fecha_inicio and r.fecha_fin and r.fecha_inicio > r.fecha_fin:
                raise UserError(_("La fecha fin tiene que ser igual o posterior a la fecha inicio."))
                
    @api.model
    def create(self, vals):
        res = super(TecnicoCalendario, self).create(vals)
        if 'fecha_inicio' in vals:
            res.actualizar_deadline_tareas('activacion')
        
        if 'fecha_fin' in vals:
            res.actualizar_deadline_tareas('desactivacion')
        return res
    
    def write(self, vals):
        res = super(TecnicoCalendario, self).write(vals)
        if 'fecha_inicio' in vals:
            self.actualizar_deadline_tareas('activacion')
            
        if 'fecha_fin' in vals:
            self.actualizar_deadline_tareas('desactivacion')
        return res
    
    def actualizar_deadline_tareas(self, tipo):
        for r in self:
            tasks = self.env['project.task'].search([
                ('project_id', '=', r.project_id.id),
                ('employee_id', '=', r.employee_id.id),
                ('job_id', '=', r.job_id.id),
                ('tarea_individual', '=', True),
                ('tipo', '=', tipo)
            ])
            
            for task in tasks:
                if tipo == 'activacion':
                    fecha = r.fecha_inicio + timedelta(days=task.deadline) if r.fecha_inicio else None
                elif tipo == 'desactivacion':
                    fecha = r.fecha_fin + timedelta(days=task.deadline) if r.fecha_fin else None
                task.write({'date_deadline': fecha})
                