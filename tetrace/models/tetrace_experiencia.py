# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Experiencia(models.Model):
    _name = 'tetrace.experiencia'
    _description = "Experiencias"

    name = fields.Char("Nombre", required=True)
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo", required=True)
    project_id = fields.Many2one('project.project', string="Proyecto", required=True)
    descripcion = fields.Text('Descripción')
    experiencia_tecnico_proyecto_ids = fields.One2many('tetrace.experiencia_tecnico_proyecto', 'experiencia_id')
    
    _sql_constraints = [
        ('job_id_project_id_uniq', 'unique(job_id, project_id)', 'No puede haber más de un puesto de trabajo por proyecto.'),
    ]
            
            
class ExperienciaTecnicoProyecto(models.Model):
    _name = 'tetrace.experiencia_tecnico_proyecto'
    _description = "Experiencias técnico proyecto"
    
    experiencia_id = fields.Many2one('tetrace.experiencia', string="Experiencia", required=True, ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, ondelete="cascade")
    project_id = fields.Many2one('project.project', string="Proyecto", required=True, ondelete="cascade")
    resume_line_id = fields.Many2one('hr.resume.line', string="Experiencia", required=True, ondelete="cascade")
                