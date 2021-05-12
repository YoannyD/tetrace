# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Job(models.Model):
    _inherit = "hr.job"

    applicant_id = fields.Many2one('hr.applicant', string="Solicitud")
    task_ids = fields.One2many('project.task', 'job_id')
    sale_order_line_ids = fields.One2many('sale.order.line', 'job_id')
    tecnico_calendario_ids = fields.One2many('tetrace.tecnico_calendario', 'job_id')
    experiencia_ids = fields.One2many('tetrace.experiencia', 'job_id')
