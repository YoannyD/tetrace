# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Job(models.Model):
    _inherit = "hr.job"

    applicant_id = fields.Many2one('hr.applicant', string="Solicitud")
    task_ids = fields.One2many('project.task', 'job_id')
    sale_order_line_ids = fields.One2many('sale.order.line', 'job_id')
