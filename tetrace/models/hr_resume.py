# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    
    name = fields.Char(translate=True)
    description = fields.Text(translate=True)
    

class ResumeLineType(models.Model):
    _inherit = 'hr.resume.line.type'

    name = fields.Char(translate=True)
    tetrace_resume_line = fields.One2many('tetrace.resume.line', 'line_type_id')
