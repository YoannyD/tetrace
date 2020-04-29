# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = "account.account"

    tetrace_account_id = fields.Many2one('tetrace.account', string="Cuenta Tetrace")


class TetraceAccount(models.Model):
    _name = "tetrace.account"
    _description = "Cuentas Tetrace"

    name = fields.Char('Nombre', required=True)
    account_ids = fields.One2many('account.account', 'tetrace_account_id')
