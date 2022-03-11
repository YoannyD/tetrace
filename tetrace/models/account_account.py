# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = "account.account"

    tetrace_account_id = fields.Many2one('tetrace.account', string="Cuenta Consolidación")
    gestionar_cartera = fields.Boolean('Gestionar cartera')


class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    exportacion = fields.Boolean("Impresos de exportación")
    
    
class TetraceAccount(models.Model):
    _name = "tetrace.account"
    _description = "Cuentas Tetrace"

    name = fields.Char('Nombre', required=True)
    code = fields.Char('Code')
    grupo_id = fields.Many2one("tetrace.grupo_tetrace_account", string="Grupo")
    account_ids = fields.One2many('account.account', 'tetrace_account_id')
    account_move_line_ids = fields.One2many('account.account', 'tetrace_account_id')
    
    
class grupo_tetrace_account(models.Model):
    _name = "tetrace.grupo_tetrace_account"
    _description = "Grupo Tetrace"
    
    name = fields.Char("Nombre", required=True)

    