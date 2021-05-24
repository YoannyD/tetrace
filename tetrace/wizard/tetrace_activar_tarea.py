# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError

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
    viaje = fields.Boolean("¿Necesita viaje?")
    baja_tecnico = fields.Boolean("Damos de baja técnico")
    baja_it = fields.Boolean("Damos de baja IT")
    recogida_equipos = fields.Boolean("Recogida de equipos")
    facturacion = fields.Boolean("Cerrar facturación")
    reubicacion_puesto = fields.Boolean("Reubicación puesto")
    project_id = fields.Many2one("project.project", string="Proyecto", ondelete="cascade")
    motivo_cancelacion_id = fields.Many2one('tetrace.motivo_cancelacion', string="Motivo cancelación")
    
    def action_activar_tareas(self):
        self.ensure_one()
        opciones = []
        if self.viaje: opciones.append('viaje')
        if self.baja_tecnico: opciones.append('baja')
        if self.baja_it: opciones.append('informatica')
        if self.recogida_equipos: opciones.append('equipos')
        if self.reubicacion_puesto: opciones.append('reubicacion')
        if self.facturacion: opciones.append('facturacion')
        
        if opciones:
            domain = [
                ('project_id', '=', self.project_id.id),
                ('tipo', '=', 'desactivacion'),
                ('activada', '=', False),
                ('opciones_desactivacion', 'in', opciones)
            ]
            tasks = self.env['project.task'].search(domain)
            for task in tasks:
                task.write({
                    'activada': True,
                    'date_deadline': fields.Date.from_string(self.fecha_fin) + timedelta(days=task.deadline_fin)
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