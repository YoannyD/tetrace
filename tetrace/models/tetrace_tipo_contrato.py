# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class TipoContrato(models.Model):
    _name = 'tetrace.tipo_contrato'
    _description = "Tipos de contrato"

    name = fields.Char('Nombre')
    contract_ids = fields.One2many('hr.contract', 'tipo_contrato_id')
