# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import re
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

_logger = logging.getLogger(__name__)


class PrevisionFacturacion(models.Model):
    _name = "tetrace.prevision_facturacion"
    _description = "Gestion facturación"
    _order = "fecha desc"
    
    order_id = fields.Many2one("sale.order", string="Pedido Venta")
    order_date_order = fields.Datetime(related="order_id.date_order", store=True)
    order_partner_id = fields.Many2one(related="order_id.partner_id", store=True)
    order_amount_total = fields.Monetary(realted="order_id.partner_id", store=True)
    order_nombre_proyecto = fields.Char(related="order_id.nombre_proyecto", store=True)
    order_project_estado_id = fields.Many2one("tetrace.project_state", 
                                              related="order_id.project_estado_id", store=True)
    fecha = fields.Date('Fecha')
    importe = fields.Monetary("Importe previsto")
    currency_id = fields.Many2one(related='order_id.currency_id')
    facturado = fields.Boolean("Facturado")
    feedbak = fields.Text("Feedbak", translate=True)
    observaciones = fields.Text("Observaciones", translate=True)
    importe_factura = fields.Monetary("Importe factura")
    no_aplica = fields.Boolean("No aplica")
    cancelado = fields.Boolean("Cancelado")