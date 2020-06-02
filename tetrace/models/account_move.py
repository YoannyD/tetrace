# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    asiento_anticipo_id = fields.Many2one('account.move', domain=[('type', '=', 'entry')], string="Asiento anticipo")
    fecha_vencimiento_anticipo = fields.Date("Fecha vencimiento anticipo",
                                             compute="_compute_fecha_vencimiento_anticipo")
    incoterm_complemento = fields.Char('Complemento Incoterm')

    def _compute_fecha_vencimiento_anticipo(self):
        for r in self:
            fecha_vencimiento_anticipo = None
            for line in r.line_ids:
                if line.date_maturity and line.account_id and line.account_id.group_id and line.account_id.group_id.code_prefix == 5200:
                    fecha_vencimiento_anticipo = line.date_maturity
                    break
            r.fecha_vencimiento_anticipo = fecha_vencimiento_anticipo
