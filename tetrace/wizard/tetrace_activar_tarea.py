# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

ACCIONES = [
    ('cancelar', 'Cancelar'),
    ('terminar', 'Terminar')
]


class ActivarTarea(models.TransientModel):
    _name = 'tetrace.activar_tarea'
    _description = "Activar tareas"
    
    fecha_fin = fields.Date("Fecha fin")
    viaje = fields.Boolean("¿Necesita viaje?")
    baja_tecnico = fields.Boolean("Damos de baja técnico")
    baja_it = fields.Boolean("Damos de baja IT")
    recogida_equipos = fields.Boolean("Recogida de equipos")
    facturacion = fields.Boolean("Cerrar facturación")
    reubicacion_puesto = fields.Boolean("Reubicación puesto")
    project_id = fields.Many2one("project.project", string="Proyecto", ondelete="cascade")
    
    def action_activar_tareas(self):
        self.ensure_one()

        domain = [
            ('project_id', '=', self.project_id.id),
            ('tipo', '=', 'desactivacion'),
            ('activada', '=', False)
        ]
        
        if self.viaje: domain += [('opciones_desactivacion', '=', 'viaje')]
        if self.baja_tecnico: domain += [('opciones_desactivacion', '=', 'baja')]
        if self.baja_it: domain += [('opciones_desactivacion', '=', 'informatica')]
        if self.recogida_equipos: domain += [('opciones_desactivacion', '=', 'equipos')]
        if self.reubicacion_puesto: domain += [('opciones_desactivacion', '=', 'reubicacion')]
        if self.facturacion: domain += [('opciones_desactivacion', '=', 'facturacion')]
            
        tasks = self.env['project.task'].search(domain)
        tasks.write({
            'activada': True,
            'date_deadline': fields.Date.from_string(self.fecha_fin) - timedelta(days=self.project_id.offset_deadline_activacion)
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