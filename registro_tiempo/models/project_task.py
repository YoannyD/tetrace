# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Entrega(models.Model):
    _inherit = 'project.task.entrega'
    
    def action_tiempo_view(self):
        tiempos = self.env['registro_tiempo.tiempo'].search([
            ('employee_id', '=', self.employee_id.id),
            ('project_id', '=', self.task_id.project_id.id)
        ])
        
        tiempo_ids = []
        for tiempo in tiempos:
            if (self.fecha_inicio >= tiempo.fecha_entrada and self.fecha_inicio <= tiempo.fecha_salida) or \
                (self.fecha_fin >= tiempo.fecha_entrada and self.fecha_fin <= tiempo.fecha_salida) or \
                (self.fecha_inicio <= tiempo.fecha_entrada and self.fecha_fin >= tiempo.fecha_salida):
                tiempo_ids.append(tiempo.id)
        
        return {
            'name': _('Horas técnico'),
            'view_mode': 'tree,form',
            'res_model': 'registro_tiempo.tiempo',
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', tiempo_ids)],
        }