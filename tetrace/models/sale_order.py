# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ref_proyecto = fields.Char('Referencia proyecto')
    descripcion_proyecto = fields.Char('Descripción proyecto')
    cabecera_proyecto = fields.Html('Cabecera proyecto')

    _sql_constraints = [
        ('ref_proyecto_uniq', 'unique (ref_proyecto)', "¡La referencia de proyecto tiene que ser única!"),
    ]
