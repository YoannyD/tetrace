# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class PickingReport(models.AbstractModel):
    _name = 'report.tetrace.stock_picking_unit'
    _description = "Informe unificado"
    
    def _get_report_values(self, docids, data):
        docs = self.env['stock.picking'].sudo().browse(docids)
        partner = None
        if docs:
            partner = docs[0].partner_id
        
        _logger.warning(docs)
        _logger.warning(partner)
        
        return {
            'docs': docs,
            'partner': partner,
            'data': data,
        }