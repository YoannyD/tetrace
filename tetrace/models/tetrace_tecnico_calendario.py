# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TecnicoCalendario(models.Model):
    _name = 'tetrace.tecnico_calendario'
    _description = "Técnicos calendarios"

    project_id = fields.Many2one('project.project', string="Proyecto", required=True)
    employee_id = fields.Many2one('hr.employee', string="Técnico", required=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string="Calendario", required=True)
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    
    @api.constrains("fecha_inicio", "fecha_fin")	
    def _check_fechas(self):
        for r in self:
            if r.fecha_inicio and r.fecha_fin and r.fecha_inicio > r.fecha_fin:
                raise UserError(_("La fecha fin tiene que ser igual o posterior a la fecha inicio."))
                