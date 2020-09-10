# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrearVersion(models.TransientModel):
    _name = 'tetrace.crear_version'
    _description = "Crear versiones"

    sale_order_id = fields.Many2one('sale.order', string="Presupuesto/Pedido de venta", ondelete="cascade")
    version = fields.Integer('Versión')
    comentarios = fields.Text('Comentarios')

    def action_crear_version(self):
        self.env['tetrace.sale_order_version'].create({
            'sale_order_id': self.sale_order_id.id,
            'comentarios': self.comentarios,
        })

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
