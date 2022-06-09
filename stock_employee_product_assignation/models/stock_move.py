# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    assignation_request_id = fields.Many2one('stock.product.assignation.request', 'Assignation Request')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _action_done(self):
        res = super(StockMoveLine, self)._action_done()
        assignation_obj = self.env['stock.product.assignation']
        for move_line in self:
            if move_line.picking_id.assignation_request_id:
                for i in range(int(move_line.qty_done)):
                    values = {}
                    values['request_id'] = move_line.picking_id.assignation_request_id.id
                    values['move_line_id'] = move_line.id
                    values['product_id'] = move_line.product_id.id
                    assignation_obj.create(values)
