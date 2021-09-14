# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"
    
    efectivacliente_date = fields.Datetime(string="Fecha efectiva cliente")
    previstacliente_date = fields.Datetime(string="Fecha prevista cliente")
    purchase_order_ids = fields.Many2many("purchase.order", compute="_compute_orders",
                                          string="Pedidos de compra", store=True)
    sale_order_ids = fields.Many2many("sale.order", compute="_compute_orders",
                                          string="Pedidos de venta", store=True)
    
    @api.depends("move_lines.purchase_line_id.order_id", "move_lines.sale_line_id.order_id")
    def _compute_orders(self):
        for r in self:
            purchase_order_ids = []
            sale_order_ids = []
            for move_line in r.move_lines:
                if move_line.purchase_line_id and move_line.purchase_line_id.order_id:
                    purchase_order_ids.append(move_line.purchase_line_id.order_id.id)
                    
                if move_line.sale_line_id and move_line.sale_line_id.order_id:
                    sale_order_ids.append(move_line.sale_line_id.order_id.id)
            r.update({
                'purchase_order_ids': [(6, 0, purchase_order_ids)],
                'sale_order_ids': [(6, 0, sale_order_ids)],
            })
    
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
