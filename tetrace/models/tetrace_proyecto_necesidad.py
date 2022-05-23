# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ProcesoSeleccion(models.Model):
    _name = "tetrace.proyecto_necesidad"
    _description = "Necesidades proyectos"
    
    project_id = fields.Many2one('project.project', string="Proyecto")
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    nacionalidad = fields.Many2one('res.country', string="Nacionalidad")
    maquina = fields.Char("Maquinas")
    salario = fields.Integer("Salario")
    formacion = fields.Many2many("hr.applicant.category", string="Formación")
    fecha_entrega = fields.Date("Fecha entrega")
    necesidad = fields.Integer("Necesidad")
    realizado = fields.Boolean("Realizado")
    observaciones = fields.Text("Observaciones")
    
    @api.model
    def create(self, vals):
        res = super(ProcesoSeleccion, self).create(vals)
        res.create_task_activity("create")
        return res
    
    def write(self, vals):
        res = super(ProcesoSeleccion, self).write(vals)
        self.create_task_activity("update")
        return res
    
    def create_task_activity(self, accion):
        for r in self:
            if not r.project_id or r.realizado:
                continue
            
            sumanry = None
            if accion == "create":
                summary = _('Gestionar necesidad del proyecto %s' % r.project_id.name)
            elif accion == "update":
                summary = _('Gestionar modificación necesidad del proyecto %s' % r.project_id.name)
                
            tasks = self.env['project.task'].search([
                ('project_id', '=', r.project_id.id),
                ('activada', 'in', [True, False]),
                ('busqueda_perfiles', '=', True)
            ])
            if tasks:
                tasks.create_activity(summary)