# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class GenerarPrevisionFacturacion(models.TransientModel):
    _name = 'tetrace.generar_prevision_facturacion'
    _description = "Generar previsión facturación"
    
    order_id = fields.Many2one("sale.order", string="Pedido Venta", ondelete="cascade")
    fecha = fields.Date("Fecha inicial")
    num_meses = fields.Integer("Número de repeticiones")
    importe = fields.Monetary("Importe")
    currency_id = fields.Many2one(related="order_id.currency_id")
    
    def action_generar(self):
        self.ensure_one()
        fecha = self.fecha
        for i in range(self.num_meses):
            fecha = self.fecha + relativedelta(months=i)
            self.env["tetrace.prevision_facturacion"].create({
                'order_id': self.order_id.id,
                'fecha': fecha,
                'importe': self.importe
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