# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

RANGOS= [
    ('0', 'Nivel 0'),
    ('1', 'Nivel 1'),
    ('2', 'Nivel 2'),
    ('3', 'Nivel 3'),
    ('4', 'Nivel 4'),
    ('5', 'Nivel 5'),
]

class User(models.Model):
    _inherit = "res.users"

    validacion_user_ids = fields.One2many('tetrace.validacion_user', 'user_id')
    rango_validaciones = fields.Selection(RANGOS, string="Rango")
