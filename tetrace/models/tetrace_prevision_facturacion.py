# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import re
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

_logger = logging.getLogger(__name__)

STATES_INVOICE = [
    ('validated', 'Validado'),
    ('without_validation', 'Sin validación'),
    ('need_validation', 'Necesita validación'),
    ('rejected', 'Rechazado'),
]

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
    invoice_ids = fields.Many2many('account.move', 'prev_fact_inv_rel', 'prev_fact_id', 'inv_id', 
                                   compute="_compute_invoice_ids", store=True)
    invoice_id = fields.Many2one('account.move', string="Factura")
    invoice_state_validation = fields.Selection(STATES_INVOICE, store=True, string="Estado validación",
                                                compute="_compute_invoice_state_validation")
    invoice_estado_tetrace = fields.Selection(related="invoice_id.estado_tetrace", store=True)
    fecha = fields.Date('Fecha')
    importe = fields.Monetary("Importe previsto")
    currency_id = fields.Many2one(related='order_id.currency_id')
    facturado = fields.Boolean("Facturado")
    feedbak = fields.Text("Feedbak", translate=True)
    observaciones = fields.Text("Observaciones", translate=True)
    importe_factura = fields.Monetary("Importe factura")
    no_aplica = fields.Boolean("No aplica")
    cancelado = fields.Boolean("Cancelado")
    company_id = fields.Many2one('res.company', string="Compañia")
    coordinador_proyecto_id = fields.Many2one("res.users", string="Coordinador proyecto")
    
    @api.depends('order_id.invoice_ids')
    def _compute_invoice_ids(self):
        for r in self:
            r.invoice_ids = r.order_id.invoice_ids.ids
            
    @api.depends('invoice_id', 'invoice_id.validated', 'invoice_id.need_validation', 
                 'invoice_id.rejected', 'invoice_id.review_ids')
    def _compute_invoice_state_validation(self):
        for r in self:
            if not r.invoice_id:
                r.invoice_state_validation = None
            elif r.invoice_id.validated:
                r.invoice_state_validation = 'validated'
            elif r.invoice_id.rejected:
                r.invoice_state_validation = 'rejected'
            elif r.invoice_id.need_validation:
                r.invoice_state_validation = 'without_validation'
            elif r.invoice_id.review_ids:
                r.invoice_state_validation = 'need_validation'
            
            