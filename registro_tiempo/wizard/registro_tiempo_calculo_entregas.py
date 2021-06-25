# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class CalculoEntregas(models.TransientModel):
    _name = 'registro_tiempo.calculo_entregas'
    _description = 'Calcular entregas'
    
    entrega_id = fields.Many2one('project.task.entrega', ondelete="cascade", string="Tarea")
    fecha_inicio = fields.Date('Fecha inicio', required=True)
    fecha_fin = fields.Date('Fecha fin', required=True)
    
    @api.constrains("fecha_inicio", "fecha_fin")
    def _check_fechas(self):
        for r in self:
            if r.fecha_inicio and r.fecha_fin and r.fecha_inicio > r.fecha_fin:
                raise ValidationError(_("La fecha de fin tiene que se superior a la de inicio"))
    
    def action_calcular(self):
        task = self.entrega_id.task_id
        if task.tarea_exceso_id:
            entrega = self.env['project.task.entrega'].search([
                ('task_id', '=', task.id),
                ('employee_id', '=', self.entrega_id.employee_id.id),
            ], limit=1)
        else:
            entrega = self.entrega_id
            
        if not entrega:
            return
        
        tiempo_ids = self.entrega_id.search_tiempos(self.fecha_inicio, self.fecha_fin)
        tiempos = self.env['registro_tiempo.tiempo'].browse(tiempo_ids)

        horas = 0
        if tiempos:
            if task.variable_facturacion == 'horas_laborables':
                horas = sum(tiempos.mapped("horas_trabajadas"))
            elif task.variable_facturacion == 'horas_extra':
                horas = sum(tiempos.mapped("horas_extra"))

        if task.exceso_facturacion == 'aumentar_entrega':
            if task.min_horas_facturacion >= horas:
                entregado = task.min_horas_facturacion
            else:
                horas_exceso = horas - task.min_horas_facturacion
                entregado = entrega.entregado + horas_exceso
                
            entrega.write({'entregado': entregado})
        elif task.exceso_facturacion == 'obviar':
            entrega.write({'entregado': task.min_horas_facturacion})
            
        self.entrega_id.write({
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
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