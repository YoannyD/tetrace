# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

TIPOS_AUSENCIAS = [
    ('rotacion', _("Rotación")),
    ('formacion', _("Formación")),
    ('permiso', _("Permiso")),
]


class Ausencia(models.Model):
    _name = "tetrace.ausencia"
    _description = "Ausencias"
    
    task_id = fields.Many2one('project.task', string="Tarea")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    ausencia = fields.Selection(TIPOS_AUSENCIAS, string="Tipo ausencia")
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_fin = fields.Date("Fecha fin")