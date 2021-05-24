# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta, datetime

_logger = logging.getLogger(__name__)

ACCIONES = [
    ('activacion', _('Activación')),
    ('desactivacion', _('Desactivación'))
]


class CrearTareasActDesc(models.TransientModel):
    _name = 'tetrace.crear_tareas_act_desc'
    _description = "Generar tareas"

    project_id = fields.Many2one('project.project', string="Proyecto", ondelete="cascade", required=True)
    accion = fields.Selection(ACCIONES, string="Acción")
    project_theme_id = fields.Many2one('project.project', string="Plantilla proyecto", ondelete="cascade")
    puesto_ids = fields.One2many('tetrace.tareas_act_puesto', 'tarea_act_id')
    tecnico_ids = fields.Many2many('hr.employee', string="Técnicos")
    tecnico_project_ids = fields.Many2many('hr.employee', compute="_compute_tecnico_project_ids",
                                           string="Técnicos proyecto")

    @api.depends('project_id')
    def _compute_tecnico_project_ids(self):
        for r in self:
            r.tecnico_project_ids = [tc.employee_id.id for tc in self.project_id.tecnico_calendario_ids]

    def action_generar_tareas(self):
        self.ensure_one()
        if self.accion == 'activacion':
            self.crear_tareas_activacion()
        elif self.accion == 'desactivacion':
            self.crear_tareas_desactivacion()

    def crear_tareas_activacion(self):
        self.ensure_one()
        ref = datetime.now().timestamp()
        for task in self.project_theme_id.tasks:
            ref_created = "%s-%s-%s" % (self.project_id.sale_order_id.id, task.project_id.id, task.id)
            if task.tarea_individual:
                for puesto in self.puesto_ids:
                    for i in range(0, puesto.cantidad):
                        ref_individual = "%s.%s.%s-%s" % (ref, puesto.employee_id.id, puesto.job_id.id, i)
                        ref_created = "%s-%s-%s" % (self.project_id.sale_order_id.id, task.project_id.id, task.id)
                        if task.check_task_exist(ref_created, ref_individual):
                            break

                        if puesto.job_id.id:
                            name = "%s (%s)" % (task.name, puesto.job_id.name)
                        else:
                            name = task.name
                            
                        values.update({
                            'name': name,
                            'job_id': puesto.job_id.id,
                            'employee_id': puesto.employee_id.id,
                            'project_id': self.project_id.id,
                            'ref_individual': ref_individual,
                            'desde_plantilla': True,
                            "company_id": self.project_id.company_id.id,
                            'ref_created': ref_created
                        })
                        
                        responsable_id, seguidores_ids = task.get_responsable_y_seguidores() 
                        if responsable_id:
                            values.update({'user_id': responsable_id})

                        new_task = task.with_context(mail_notrack=True).copy(values)
                        if seguidores_ids:
                            new_task.with_context(add_follower=True).message_subscribe(seguidores_ids, [])
                        
            elif not task.check_task_exist(ref_created):
                responsable_id, seguidores_ids = task.get_responsable_y_seguidores()  
                new_task = task.copy({
                    'name': task.name,
                    'sale_line_id': None,
                    'partner_id': responsable_id,
                    'email_from': self.project_id.sale_order_id.partner_id.email,
                    'desde_plantilla': True,
                    'project_id': self.project_id.id,
                    "company_id": self.project_id.company_id.id,
                    'ref_created': ref_created
                })
                
                if seguidores_ids:
                    new_task.with_context(add_follower=True).message_subscribe(seguidores_ids, [])

    def crear_tareas_desactivacion(self):
        self.ensure_one()
        tareas = self.env['project.task'].search([
            ('project_id', '=', self.project_id.id),
            ('employee_id', 'in', self.tecnico_ids.ids),
            ('activada', '=', False)
        ])
        tareas.write({'activada': True})

    def open_wizard(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }


class TareasActPuesto(models.TransientModel):
    _name = 'tetrace.tareas_act_puesto'
    _description = "Crear tareas Activacion puestos empleados"

    tarea_act_id = fields.Many2one('tetrace.crear_tareas_act_desc', string="Wizard creación")
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    cantidad = fields.Integer('Cantidad')
