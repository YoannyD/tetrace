# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProcesoSeleccion(models.Model):
    _name = "tetrace.proceso_seleccion"
    _description = "Proceso Seleccion"

    name = fields.Char('Nombre', required=True, translate=True)