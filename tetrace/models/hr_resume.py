# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResumeLineType(models.Model):
    _inherit = 'hr.resume.line.type'

    tetrace_resume_line = fields.One2many('tetrace.resume.line', 'line_type_id')
