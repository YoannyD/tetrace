# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    cuenta_activo = fields.Boolean('Activo')
    
    @api.model
    def create(self, vals):
        res = super(PurchaseOrderLine, self).create(vals)
        res.actualizar_cuenta_activo()
        return res
        
    def write(self, vals):
        res = super(PurchaseOrderLine, self).write(vals)
        self.actualizar_cuenta_activo()
        return res
        
    def actualizar_cuenta_activo(self):
        for r in self:
            if r.order_id.order_line.filtered(lambda x: not x.cuenta_activo):
                r.order_id.write({'cuenta_activo': False})
    
    def _prepare_account_move_line(self, move):
        self.ensure_one()
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if self.cuenta_activo and self.product_id.categ_id:
            res.update({'account_id': self.product_id.categ_id.account_activo_id.id})
        return res