# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)



class PCR(models.Model):
    _name = "tetrace.pcr"
    _description = "PCRs"
    
    task_id = fields.Many2one('project.task', string="Tarea")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    employee_active_ids = fields.Many2many("hr.employee", related="task_id.project_id.tecnico_ids")
    fecha = fields.Date("Fecha")
    realizado = fields.Boolean("Realizado")