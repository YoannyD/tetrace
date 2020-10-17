# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = "res.users"

    validacion_user_ids = fields.One2many('tetrace.validacion_user', 'user_id')
    rango_validaciones = fields.Integer("Rango")
