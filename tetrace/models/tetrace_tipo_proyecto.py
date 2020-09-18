# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TipoProyecto(models.Model):
    _name = "tetrace.tipo_proyecto"
    _description = "Tipos de proyecto"

    name = fields.Char('Nombre', required=True)
    tipo = fields.Char('Tipo', required=True)
    sale_order_ids = fields.One2many('sale.order', 'tipo_proyecto_id')

    @api.constrains("tipo")
    def _check_tipo(self):
        for r in self:
            if r.tipo and len(r.tipo) != 2:
                raise UserError('El tipo tiene que ser 2 caracteres.')
