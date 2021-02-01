# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = "res.company"

    tetrace_tickelia_journal_id = fields.Many2one('account.journal', string='Diario de liquidaciones Tickelia')
    tetrace_nomina_journal_id = fields.Many2one('account.journal', string='Diario de liquidaciones (Nóminas)')
    tetrace_cuenta_analitica_diferencia_cambio = fields.Many2one('account.analytic.account', 
                                                                 string='Cuenta anlítica apuntes diferencias de cambio')
    grupo_tetrace = fields.Boolean("Grupo Tetrace")
