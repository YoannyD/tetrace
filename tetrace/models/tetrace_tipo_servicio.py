# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class TipoServicio(models.Model):
    _name = "tetrace.tipo_servicio"
    _description = "Tipos de servicio"

    name = fields.Char('Nombre', required=True, translate=True)
    sale_order_ids = fields.One2many('sale.order', 'tipo_proyecto_id')
    color = fields.Integer(string='Color Index')
    tipo_proyecto_ids = fields.Many2many('tetrace.tipo_proyecto')
