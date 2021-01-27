# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Departament(models.Model):
    _inherit = "hr.department"
    
    task_ids = fields.One2many("project.task", "department_id")
    laboral = fields.Boolean("Laboral")