# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import base64

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderVersion(models.Model):
    _name = 'tetrace.sale_order_version'
    _description = 'Versiones de presupuestos/pedidos de venta'
    _order = "version desc, create_date"

    name = fields.Char('Nombre', compute="_compute_name", store=True)
    version = fields.Integer('Versión')
    sale_order_id = fields.Many2one('sale.order', string="Presupuesto/Pedido de venta", required=True)
    comentarios = fields.Char('Comentarios', translate=True)
    pdf = fields.Binary('PDF')

    @api.depends('version', 'comentarios', 'create_date')
    def _compute_name(self):
        for r in self:
            r.name = "[v%s] %s %s" % (r.version, r.comentarios, fields.Datetime.to_string(r.create_date))

    @api.model
    def create(self, vals):
        version = self.siguiente_version(vals.get('sale_order_id'))
        pdf = self.crear_pdf(vals.get('sale_order_id'))

        vals.update({
            'version': version,
            'pdf': pdf
        })
        res = super(SaleOrderVersion, self).create(vals)
        return res

    def siguiente_version(self, order_id):
        version = self.search([('sale_order_id', '=', order_id)], limit=1)
        if version:
            return version.version + 1
        return 1

    def crear_pdf(self, order_id):
        order = self.env['sale.order'].browse(order_id)
        if order.visible_btn_generar_proyecto or order.project_ids:
            name_report = "tetrace.report_saleorder_proyecto"
        else:
            name_report = "sale.report_saleorder"
            
        report = self.env["ir.actions.report"]._get_report_from_name(name_report)
        pdf_bin, _ = report.render_qweb_pdf(order_id)
        return base64.b64encode(pdf_bin)
