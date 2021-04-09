# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Festivo(models.Model):
    _name = "tetrace.festivo"
    _description = "Festivos"

    name = fields.Char('Descripción')
    country_id = fields.Many2one('res.country', string="País", required=True)
    fecha_inicio = fields.Date('Fecha inicio', required=True)
    fecha_fin = fields.Date('Fecha fin', required=True)

