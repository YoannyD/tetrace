# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"
    
    efectivacliente_date = fields.Datetime(string="Fecha efectiva cliente")
    previstacliente_date = fields.Datetime(string="Fecha prevista cliente")
      
    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        warehouse = self.picking_type_id.warehouse_id
        if self.picking_type_id.sequence_code == "OUT" and warehouse and warehouse.responsable_exportacion_id:
            self.user_id = warehouse.responsable_exportacion_id.id
    
    @api.model
    def create(self, vals):
        res = super(Picking, self).create(vals)
        if not res.user_id:
            res._onchange_picking_type_id()
        return res
