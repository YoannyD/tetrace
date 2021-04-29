# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ChangePartnerSaleOrder(models.TransientModel):
    _name = 'tetrace.change_partner_sale_order'
    _description = "Cambiar cliente del Pedido de venta"
    
    order_id = fields.Many2one('sale.order', string="Pedido de venta", required=True, ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string="Cliente")
    
    def action_change_partner(self):
        self.ensure_one()
        self.order_id.write({'partner_id': self.partner_id.id})
        self.order_id.onchange_partner_id()
        self.order_id.onchange_partner_shipping_id()
    
    def open_wizard(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }