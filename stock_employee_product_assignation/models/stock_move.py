# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    assignation_request_id = fields.Many2one('stock.product.assignation.request', 'Assignation Request')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _action_done(self):
        assignation_obj = self.env['stock.product.assignation']
        location_destiny = self.env.ref('stock_employee_product_assignation.stock_location_employee_assignation')
        for move_line in self:
            if move_line.picking_id.assignation_request_id and move_line.picking_id.location_id != location_destiny:
                for i in range(int(move_line.qty_done)):
                    values = {}
                    values['request_id'] = move_line.picking_id.assignation_request_id.id
                    values['move_line_id'] = move_line.id
                    values['product_id'] = move_line.product_id.id
                    values['assignation_return'] = False
                    if move_line.picking_id.assignation_request_id.task_id:
                        values['task_id'] = move_line.picking_id.assignation_request_id.task_id.id
                    if move_line.tracking in ['serial', 'lot']:
                        values['code'] = move_line.lot_id.name
                        values['code_readonly'] = True
                    assignation_obj.create(values)
        res = super(StockMoveLine, self)._action_done()
        return res