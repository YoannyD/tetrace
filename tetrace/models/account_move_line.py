# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    categoria_ids = fields.Many2many('account.move.line.category')


class CategoriaMoveLine(models.Model):
    _name = "account.move.line.category"
    _description = "Categorías de las líneas de movimiento"

    name = fields.Char('Nombre', required=True)
    move_line_ids = fields.Many2many('account.move.line')
