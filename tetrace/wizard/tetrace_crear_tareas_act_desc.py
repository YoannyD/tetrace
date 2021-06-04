# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta, datetime
from odoo.addons.tetrace.models.tetrace_ausencia import TIPOS_AUSENCIAS

_logger = logging.getLogger(__name__)

ACCIONES = [
    ('activacion', _('Activación')),
    ('desactivacion', _('Desactivación')),
    ('ausencia', _('Ausencia')),
]


class CrearTareasActDesc(models.TransientModel):
    _name = 'tetrace.crear_tareas_act_desc'
    _description = "Generar tareas"

    project_id = fields.Many2one('project.project', string="Proyecto", ondelete="cascade", required=True)
    accion = fields.Selection(ACCIONES, string="Acción")
    project_theme_id = fields.Many2one('project.project', string="Plantilla proyecto", ondelete="cascade")
    detalle_act_ids = fields.One2many('tetrace.detalle_act', 'tarea_act_id')
    detalle_desc_ids = fields.One2many('tetrace.detalle_desc', 'tarea_act_id')
    detalle_ausencia_ids = fields.One2many('tetrace.detalle_ausencia', 'tarea_act_id')
    tecnico_ids = fields.Many2many('hr.employee', compute="_compute_tecnico_ids", store=True)
    viaje_ids = fields.One2many('tetrace.tareas_act_viaje', 'tarea_act_id')
    alojamiento_ids = fields.One2many('tetrace.tareas_act_alojamiento', 'tarea_act_id')
    alquiler_ids = fields.One2many('tetrace.tareas_act_alquiler', 'tarea_act_id')
    viaje = fields.Boolean("Trips")

    @api.depends("project_id.tecnico_calendario_ids")
    def _compute_tecnico_ids(self):
        for r in self:
            r.tecnico_ids = [(6, 0, [d.employee_id.id for d in r.project_id.tecnico_calendario_ids])]

    def action_generar_tareas(self):
        self.ensure_one()
        if self.accion == 'activacion':
            self.crear_tareas_activacion()
        elif self.accion == 'desactivacion':
            self.crear_tareas_desactivacion()
        elif self.accion == 'ausencia':
            self.crear_tareas_ausencia()
            
        tasks = self.env['project.task'].search([
            ('viajes', '=', True),
            ('project_id', '=', self.project_id.id)
        ])
        for task in tasks:
            for viaje in self.viaje_ids:
                self.env["tetrace.viaje"].create({
                    'task_id': task.id,
                    'fecha': viaje.fecha,
                    'origen': viaje.origen,
                    'destino': viaje.destino,
                    'contratado': viaje.contratado,
                    'realizado': viaje.realizado,
                    'fecha': viaje.fecha,
                    'employee_id': viaje.employee_id.id if viaje.employee_id else None,
                    'observaciones': viaje.observaciones
                })

            for alojamiento in self.alojamiento_ids:
                self.env["tetrace.alojamiento"].create({
                    'task_id': task.id,
                    'fecha': alojamiento.fecha,
                    'fecha_fin': alojamiento.fecha_fin,
                    'ciudad': alojamiento.ciudad,
                    'completado': alojamiento.completado,
                    'realizado': alojamiento.realizado,
                    'fecha': alojamiento.fecha,
                    'employee_id': alojamiento.employee_id.id if alojamiento.employee_id else None,
                    'observaciones': viaje.observaciones
                })
                
            for alquiler in self.alquiler_ids:
                self.env["tetrace.alquiler_vehiculo"].create({
                    'task_id': task.id,
                    'fecha_inicio': alquiler.fecha_inicio,
                    'fecha_fin': alquiler.fecha_fin,
                    'recogida': alquiler.recogida,
                    'entrega': alquiler.entrega,
                    'realizado': alquiler.realizado,
                    'completado': alquiler.completado,
                    'employee_id': alquiler.employee_id.id if alquiler.employee_id else None,
                    'observaciones': alquiler.observaciones
                })

    def crear_tareas_activacion(self):
        self.ensure_one()
        ref = datetime.now().timestamp()
        for task in self.project_theme_id.tasks:
            ref_created = "%s-%s-%s" % (self.project_id.sale_order_id.id, task.project_id.id, task.id)
            if task.tarea_individual:
                for detalle in self.detalle_act_ids:
                    ref_individual = "%s.%s.%s-%s" % (ref, detalle.employee_id.id, detalle.job_id.id, 1)
                    ref_created = "%s-%s-%s" % (self.project_id.sale_order_id.id, task.project_id.id, task.id)
                    if task.check_task_exist(ref_created, ref_individual):
                        break

                    if detalle.job_id.id:
                        name = "%s (%s)" % (task.name, detalle.job_id.name)
                    else:
                        name = task.name
                            
                    values = {
                        'name': name,
                        'job_id': detalle.job_id.id,
                        'employee_id': detalle.employee_id.id,
                        'project_id': self.project_id.id,
                        'ref_individual': ref_individual,
                        'desde_plantilla': True,
                        "company_id": self.project_id.company_id.id,
                        'ref_created': ref_created
                    }
                        
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
        for detalle in self.detalle_desc_ids:
            opciones = []
            if detalle.baja_it: opciones.append('informatica')
            if detalle.recoger_equipos: opciones.append('equipos')
            if detalle.reubicar: opciones.append('reubicacion')
            if detalle.finalizar_contrato: opciones.append('facturacion')
            
            tareas = self.env['project.task'].search([
                ('tipo', '=', 'desactivacion'),
                ('opciones_desactivacion', 'in', opciones),
                ('employee_id', '=', detalle.employee_id.id),
                ('project_id', '=', self.project_id.id),
                ('activada', '=', False)
            ])
            tareas.write({'activada': True})
            
    def crear_tareas_ausencia(self):
        tareas = self.env['project.task'].search([
            ('project_id', '=', self.project_id.id),
            ('ausencia', '=', True),
        ])
        for tarea in tareas:
            for ausencia in self.detalle_ausencia_ids:
                self.env["tetrace.ausencia"].create({
                    'task_id': tarea.id,
                    'employee_id': ausencia.employee_id.id,
                    'ausencia': ausencia.ausencia,
                    'fecha_inicio': ausencia.fecha_inicio,
                    'fecha_fin': ausencia.fecha_fin,
                })

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


class DetalleActivacion(models.TransientModel):
    _name = 'tetrace.detalle_act'
    _description = "Detalles activacion"

    tarea_act_id = fields.Many2one('tetrace.crear_tareas_act_desc', string="Wizard creación")
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    resource_calendar_id = fields.Many2one('resource.calendar', string="Calendario")
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')
    

class DetalleDesactivacion(models.TransientModel):
    _name = 'tetrace.detalle_desc'
    _description = "Detalles desactivacion"

    tarea_act_id = fields.Many2one('tetrace.crear_tareas_act_desc', string="Wizard creación")
    employee_id = fields.Many2one('hr.employee', string="Técnico", required=True)
    fecha_fin = fields.Date("Fecha fin")
    finalizar_contrato = fields.Boolean("Finalizar contrato")
    reubicar = fields.Boolean("Reubicar", default=True)
    baja_it = fields.Boolean("Baja IT")
    recoger_equipos = fields.Boolean("Recoger equipos")
    
    @api.onchange("finalizar_contrato")
    def _onchange_finalizar_contrato(self):
        if self.finalizar_contrato:
            self.reubicar = False
            
    @api.onchange("reubicar")
    def _onchange_reubicar(self):
        if self.reubicar:
            self.finalizar_contrato = False
    

class DetalleAusencia(models.TransientModel):
    _name = 'tetrace.detalle_ausencia'
    _description = "Detalles ausencia"
    
    tarea_act_id = fields.Many2one('tetrace.crear_tareas_act_desc', string="Wizard creación")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    ausencia = fields.Selection(TIPOS_AUSENCIAS, string="Tipo ausencia")
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")

    
class ActivarTareaViaje(models.TransientModel):
    _name = 'tetrace.tareas_act_viaje'
    _description = "Crear tareas viajes"
    
    tarea_act_id = fields.Many2one('tetrace.crear_tareas_act_desc', string="Wizard creación")
    fecha = fields.Date("Fecha")
    origen = fields.Char("Origen", translate=True)
    destino = fields.Char("Destino", translate=True)
    contratado = fields.Boolean("Contratado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    observaciones = fields.Text("Observaciones", translate=True)
    
    
class ActivarTareaAlojamiento(models.TransientModel):
    _name = 'tetrace.tareas_act_alojamiento'
    _description = "Crear tareas alojamientos"
    
    tarea_act_id = fields.Many2one('tetrace.crear_tareas_act_desc', string="Wizard creación")
    fecha = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")
    ciudad = fields.Char("Ciudad", translate=True)
    completado = fields.Boolean("Completado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    observaciones = fields.Text("Observaciones", translate=True)
    
    @api.constrains("fecha", "fecha_fin")
    def _check_fechas(self):
        for r in self:
            if r.fecha and r.fecha_fin and r.fecha > r.fecha_fin:
                raise ValidationError(_("La fecha fin tiene que se superior a la de entrada"))
    
    
class ActivarTareaAlquiler(models.TransientModel):
    _name = 'tetrace.tareas_act_alquiler'
    _description = "Crear tareas alquiler"
    
    tarea_act_id = fields.Many2one('tetrace.crear_tareas_act_desc', string="Wizard creación")
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")
    recogida = fields.Text("Recogida", translate=True)
    entrega = fields.Text("Entrega", translate=True)
    completado = fields.Boolean("Completado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    observaciones = fields.Text("Observaciones", translate=True)
