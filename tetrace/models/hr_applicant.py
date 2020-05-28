# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Applicant(models.Model):
    _inherit = "hr.applicant"

    country_id = fields.Many2one('res.country', string="País")
    applicant_optional_ids = fields.Many2many('hr.applicant', 'rel_applicant_optional', 'apli1', 'apli2',
                                              string="Otro puesto de trabajo")
    carpeta_drive = fields.Char('Carpeta Drive')
