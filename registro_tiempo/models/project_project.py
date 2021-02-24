# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class Project(models.Model):
    _inherit = 'project.project'

    tiempo_ids = fields.One2many("registro_tiempo.tiempo", "project_id")
    tiempo_count = fields.Integer("Nº tiempos", compute="_compute_tiempo")

    @api.depends("tiempo_ids")
    def _compute_tiempo(self):
        for r in self:
            r.tiempo_count = len(r.tiempo_ids)
