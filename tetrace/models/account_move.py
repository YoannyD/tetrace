# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    asiento_anticipo_id = fields.Many2one('account.move', domain=[('type', '=', 'entry')], string="Asiento anticipo")
    incoterm_complemento = fields.Char('Complemento Incoterm')
