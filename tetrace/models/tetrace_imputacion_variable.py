# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ImputacionVariable(models.Model):
    _name = "tetrace.imputacion_variable"
    _description = "Imputaciones variables"

    name = fields.Char('Descripción')
    order_id = fields.Many2one('sale.order', string="Pedido de venta")
    product_id = fields.Many2one("product.product", string="Servicio")
    coste = fields.Monetary('Coste')
    currency_id = fields.Many2one('res.currency', related="order_id.currency_id")
    line_ids = fields.One2many("tetrace.imputacion_variable_line", "imputacion_id")
    
    def unlink(self):
        for r in self:
            r.line_ids.unlink()
        return super(ImputacionVariable, self).unlink()

    
class ImputacionVariableLine(models.Model):
    _name = "tetrace.imputacion_variable_line"
    _description = "Imputaciones variables repartición"
    
    imputacion_id = fields.Many2one("tetrace.imputacion_variable", string="Imputación variable")
    order_line_id = fields.Many2one("sale.order.line", string="Linea pedido de venta")
    order_line_product_id = fields.Many2one("product.product", related="order_line_id.product_id")
    incremento = fields.Monetary('Incremento')
    porcentaje = fields.Float("Porcentaje")
    currency_id = fields.Many2one('res.currency', related="order_line_id.currency_id")
    
    def unlink(self):
        for r in self:
            r.order_line_id.write({'price_unit': r.order_line_id.price_unit - r.incremento})
        return super(ImputacionVariableLine, self).unlink()