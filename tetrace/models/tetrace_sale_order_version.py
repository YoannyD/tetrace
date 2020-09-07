# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderVersion(models.Model):
    _name = 'tetrace.sale_order_version'
    _description = 'Versiones de presupuestos/pedidos de venta'
    _order = "create_date, version desc"


    name = fields.Char('Nombre', compute="_compute_name", store=True)
    version = fields.Integer('Versión')
    sale_order_id = fields.Many2one('sale.order', string="Presupuesto/Pedido de venta", required=True)
    comentarios = fields.Char('Comentarios')
    pdf = fields.Binary('PDF')

    @api.depends('version', 'comentarios', 'create_date')
    def _compute_name(self):
        for r in self:
            r.name = "[v%s] %s %s" % (r.version, r.comentarios, fields.Datetime.to_string(r.create_date))

    @api.model
    def create(self, vals):
        version = self.siguiente_version(vals.get('sale_order_id'))
        vals.update({'version': version})
        res = super(SaleOrderVersion, self).create(vals)
        return res

    def siguiente_version(self, order_id):
        version = self.search([('sale_order_id', '=', order_id)], limit=1)
        if version:
            return version.version + 1
        return 1
