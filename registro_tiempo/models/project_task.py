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
            ('project_id', '=', self.task_id.project_id.id),
            '&', '|',
            ('fecha_salida', '<=', self.fecha_fin),
            ('fecha_entrada', '>=', self.fecha_inicio),
            ('fecha_salida', '>=', self.fecha_fin),
            ('fecha_entrada', '<=', self.fecha_fin),
        ])
        
        return {
            'name': _('Horas técnico'),
            'view_mode': 'tree,form',
            'res_model': 'registro_tiempo.tiempo',
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', tiempos.ids)],
        }