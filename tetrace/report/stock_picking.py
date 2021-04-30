# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PickingReport(models.AbstractModel):
    _name = 'report.tetrace.stock_picking_unit'
    _description = "Informe unificado"

    def _get_report_values(self, docids, data):
        pickings = self.env['stock.picking'].sudo().search([('id', 'in', docids)])
        partner = None
        if pickings:
            partner = pickings[0].partner_id
            
        for p in pickings:
            if p.partner_id != partner:
                raise UserError(_("Los albaranes tiene que ser del mismo cliente."))

        return {
            'docs': pickings,
            'partner': partner,
            'data': data,
        }
