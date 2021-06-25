# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

FRECUENCIA_FACTURACION = [
    ('mensual', _('Mensual')),
    ('semanal', _('Semanal')),
]

VARIABLES_FACTURACION = [
    ('horas_laborables', _('Hora Laborables')),
    ('horas_extra', _('Horas extra')),
]

EXCESOS_FACTURACION = [
    ('obviar', _('Obviar')),
    ('aumentar_entrega', _('Aumentar entrega')),
]


class Task(models.Model):
    _inherit = 'project.task'
    
    frecuencia_facturacion = fields.Selection(FRECUENCIA_FACTURACION, string="Frecuencia facturación", 
                                              default="mensual")
    variable_facturacion = fields.Selection(VARIABLES_FACTURACION, string="Variable facturación")
    min_horas_facturacion = fields.Float("Mínimo horas facturación")
    exceso_facturacion = fields.Selection(EXCESOS_FACTURACION, default="obviar",
                                          string="Exceso facturación")
    tarea_exceso_id = fields.Many2one('project.task', string="Tarea exceso")


class Entrega(models.Model):
    _inherit = 'project.task.entrega'
    
    def action_tiempo_view(self):
        return {
            'name': _('Horas técnico'),
            'view_mode': 'tree,form',
            'res_model': 'registro_tiempo.tiempo',
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.search_tiempos())],
        }
    
    def search_tiempos(self, fecha_inicio, fecha_fin):
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
        return tiempo_ids
    
    def open_wizard_calculo_entregas(self):
        wizard = self.env['registro_tiempo.calculo_entregas'].create({
            'entrega_id': self.id,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
        })
        return wizard.open_wizard()