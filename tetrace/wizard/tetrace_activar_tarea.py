# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

ACCIONES = [
    ('cancelar', _('Cancelar')),
    ('terminar', _('Terminar'))
]


class ActivarTarea(models.TransientModel):
    _name = 'tetrace.activar_tarea'
    _description = "Activar tareas"
    
    accion = fields.Selection(ACCIONES, string="Acción")
    fecha_fin = fields.Date("Fecha fin")
    viaje = fields.Boolean("Trips")
    detalle_ids = fields.One2many('tetrace.activar_tarea_detalle', 'activar_tarea_id')
    tecnico_ids = fields.Many2many('hr.employee', compute="_compute_tecnico_ids", store=True)
    project_id = fields.Many2one("project.project", string="Proyecto", ondelete="cascade")
    motivo_cancelacion_id = fields.Many2one('tetrace.motivo_cancelacion', string="Motivo cancelación")
    viaje_ids = fields.One2many('tetrace.act_viaje', 'activar_tarea_id')
    alojamiento_ids = fields.One2many('tetrace.act_alojamiento', 'activar_tarea_id')
    alquiler_ids = fields.One2many('tetrace.act_alquiler', 'activar_tarea_id')

    @api.depends("detalle_ids.employee_id")
    def _compute_tecnico_ids(self):
        for r in self:
            r.tecnico_ids = [(6, 0, [d.employee_id.id for d in r.detalle_ids])]
    
    def action_activar_tareas(self):
        self.ensure_one()
        domain_base = [
            ('project_id', '=', self.project_id.id),
            ('tipo', '=', 'desactivacion'),
            ('activada', '=', False),
        ]
        
        for detalle in self.detalle_ids:
            opciones = []
            if detalle.baja_it: opciones.append('informatica')
            if detalle.recoger_equipos: opciones.append('equipos')
            if detalle.reubicar: opciones.append('reubicacion')
            if detalle.finalizar_contrato: opciones.append('facturacion')
            
            domain = expression.AND([domain_base, [
                ('opciones_desactivacion', 'in', opciones),
                ('employee_id', '=', detalle.employee_id.id)
            ]]) 
            tasks = self.env['project.task'].search(domain)
            for task in tasks:
                tasks.write({
                    'activada': True,
                    'date_deadline': fields.Date.from_string(self.fecha_fin) + timedelta(days=task.deadline)
                })
                
            if detalle.fecha_fin:
                for tc in self.project_id.tecnico_calendario_ids:
                    if not tc.fecha_fin and detalle.employee_id.id == tc.employee_id.id:
                        tc.write({'fecha_fin': detalle.fecha_fin})
        
        if self.viaje:
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
                    
                task.write({
                    'activada': True,
                    'date_deadline': fields.Date.from_string(self.fecha_fin) + timedelta(days=task.deadline)
                })
        
        values_project = {}
        if self.accion == 'cancelar':
            values_project = {
                'estado_id': 4, # Estado cancelado
                'motivo_cancelacion_id': self.motivo_cancelacion_id.id,
                'fecha_cancelacion': self.fecha_fin
            }
        elif self.accion == 'terminar':
            values_project = {
                'estado_id': 2, # Estado terminado
                'fecha_finalizacion': self.fecha_fin
            }
        
        self.project_id.write(values_project)
        
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
    
    
class ActivarTareaDetalle(models.TransientModel):
    _name = 'tetrace.activar_tarea_detalle'
    _description = "Activar tareas detalles"
    
    activar_tarea_id = fields.Many2one('tetrace.activar_tarea', string="Activar tareas", required=True)
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
    

class ActivarTareaViaje(models.TransientModel):
    _name = 'tetrace.act_viaje'
    _description = "Activar tareas viajes"
    
    activar_tarea_id = fields.Many2one('tetrace.activar_tarea', string="Detalles")
    fecha = fields.Date("Fecha")
    origen = fields.Char("Origen", translate=True)
    destino = fields.Char("Destino", translate=True)
    contratado = fields.Boolean("Contratado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    observaciones = fields.Text("Observaciones", translate=True)
    
    
class ActivarTareaAlojamiento(models.TransientModel):
    _name = 'tetrace.act_alojamiento'
    _description = "Activar tareas alojamientos"
    
    activar_tarea_id = fields.Many2one('tetrace.activar_tarea', string="Detalles")
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
    _name = 'tetrace.act_alquiler'
    _description = "Activar tareas alquiler"
    
    activar_tarea_id = fields.Many2one('tetrace.activar_tarea', string="Detalles")
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")
    recogida = fields.Text("Recogida", translate=True)
    entrega = fields.Text("Entrega", translate=True)
    completado = fields.Boolean("Completado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    observaciones = fields.Text("Observaciones", translate=True)
