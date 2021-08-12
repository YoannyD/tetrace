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
    
    order_id = fields.Many2one("sale.order", context="{'display_num_proyecto': True}", string="Pedido Venta")
    order_date_order = fields.Datetime(related="order_id.date_order", store=True)
    order_partner_id = fields.Many2one(related="order_id.partner_id", store=True)
    order_amount_total = fields.Monetary(realted="order_id.partner_id", store=True)
    order_ref_proyecto = fields.Char(related="order_id.ref_proyecto", store=True)
    order_nombre_proyecto = fields.Char(related="order_id.nombre_proyecto", store=True)
    order_project_estado_id = fields.Many2one("tetrace.project_state", 
                                              related="order_id.project_estado_id", store=True)
    order_company_id = fields.Many2one('res.company', related="order_id.company_id", store=True)
    order_coordinador_proyecto_id = fields.Many2one("res.users", related="order_id.coordinador_proyecto_id")
    invoice_ids = fields.Many2many('account.move', 'prev_fact_inv_rel', 'prev_fact_id', 'inv_id', 
                                   compute="_compute_invoice_ids", store=True)
    invoice_id = fields.Many2one('account.move', string="Factura")
    invoice_last_review_status  = fields.Char("Estado última revisión", compute="_compute_invoice_review")
    invoice_last_review_name = fields.Char("Nombre última revisión", compute="_compute_invoice_review")
    invoice_estado_tetrace = fields.Selection(related="invoice_id.estado_tetrace", store=True)
    invoice_amount_total = fields.Monetary(related="invoice_id.amount_total", store=True)
    fecha = fields.Date('Fecha')
    importe = fields.Monetary("Importe previsto")
    currency_id = fields.Many2one(related='order_id.currency_id')
    facturado = fields.Boolean("Facturado")
    feedbak = fields.Text("Feedbak", translate=True)
    observaciones = fields.Text("Observaciones", translate=True)
    no_aplica = fields.Boolean("No aplica")
    cancelado = fields.Boolean("Cancelado")
    trips = fields.Boolean("Trips")
    compras = fields.Boolean("Compras")
    coordinador = fields.Boolean("Coordinador")
    
    @api.depends('order_id.invoice_ids')
    def _compute_invoice_ids(self):
        for r in self:
            r.invoice_ids = r.order_id.invoice_ids.ids
            
    @api.depends('invoice_id.review_ids')
    def _compute_invoice_review(self):
        for r in self:
            status = None
            name = None
            if r.invoice_id:
                for review in r.invoice_id.review_ids:
                    if review.status != 'approved':
                        status = dict(review._fields['status'].selection).get(review.status)
                        name = review.name
                        break
            
            r.update({
                'invoice_last_review_status': status,
                'invoice_last_review_name': name
            })