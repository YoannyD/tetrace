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
    icono_warning = fields.Boolean('Veneno')
