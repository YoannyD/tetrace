# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tetrace_account_id = fields.Many2one("tetrace.account", string="Cuenta Tetrace", company_dependent=False,
                                         compute="_compute_tetrace_account_id", store=True)
    asiento_anticipo_id = fields.Many2one(related="move_id.asiento_anticipo_id")
    asiento_anticipo_fecha_vencimiento = fields.Date("Fecha vencimiento anticipo",
                                                     compute="_compute_asiento_anticipo_fecha_vencimiento")
    confirmado = fields.Boolean('Confirmado')

    @api.depends("account_id.tetrace_account_id")
    def _compute_tetrace_account_id(self):
        for r in self:
            r.tetrace_account_id = r.account_id.tetrace_account_id.id if r.account_id.tetrace_account_id else None

    def _compute_asiento_anticipo_fecha_vencimiento(self):
        for r in self:
            fecha_vencimiento = None
            if r.asiento_anticipo_id and r.asiento_anticipo_id.fecha_vencimiento_anticipo:
                fecha_vencimiento = r.asiento_anticipo_id.fecha_vencimiento_anticipo
            r.asiento_anticipo_fecha_vencimiento = fecha_vencimiento
