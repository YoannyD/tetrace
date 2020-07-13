# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Applicant(models.Model):
    _inherit = "hr.applicant"

    country_id = fields.Many2one('res.country', string="País")
    job_ids = fields.Many2many('hr.job', 'applicant_id', string="Otro puesto de trabajo")
    carpeta_drive = fields.Char('Carpeta Drive')
    fecha_recepcion = fields.Date('Fecha recepción')
    sin_adjuntos = fields.Boolean('Sin adjuntos en Drive')
    categ_ids = fields.Many2many(string='Formación')
    priority = fields.Selection(selection_add=[('4', 'Perfecto')], default='2')
    icono_warning = fields.Boolean('Alerta')
    referencia = fields.Char('Referencia Tetrace')
    resume_line_ids = fields.One2many('tetrace.resume.line', 'applicant_id', string="Resumé lines")
    applicant_skill_ids = fields.One2many('tetrace.applicant.skill', 'applicant_id', string="Habilidades")


class ApplicationResumeLine(models.Model):
    _name = 'tetrace.resume.line'
    _description = "Currículums vitaes"
    _order = "line_type_id, date_end desc, date_start desc"

    applicant_id = fields.Many2one('hr.applicant', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date()
    description = fields.Text(string="Description")
    line_type_id = fields.Many2one('tetrace.resume.line.type', string="Tipo")
    display_type = fields.Selection([('classic', 'Classic')], string="Display Type", default='classic')

    _sql_constraints = [
        ('date_check', "CHECK ((date_start <= date_end OR date_end = NULL))", "The start date must be anterior to the end date."),
    ]


class ApplicationResumeLineType(models.Model):
    _name = 'tetrace.resume.line.type'
    _description = "Tipos de la línea de Currículums"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer('Sequence', default=10)
