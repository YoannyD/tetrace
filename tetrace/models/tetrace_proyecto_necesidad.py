# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProcesoSeleccion(models.Model):
    _name = "tetrace.proyecto_necesidad"
    _description = "Necesidades proyectos"
    
    project_id = fields.Many2one('project.project', string="Proyecto")
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    necesidad = fields.Integer("Necesidad")
    