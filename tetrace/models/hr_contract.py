# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Contract(models.Model):
    _inherit = "hr.contract"

    tipo_contrato_id = fields.Many2one('tetrace.tipo_contrato', string="Tipo de contrato")
