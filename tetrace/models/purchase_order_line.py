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
    
    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        if self.order_id.partner_id:
            supplier_info = self.env["product.supplierinfo"].search([
                ('product_name', '!=', False),
                ('name', '=', self.order_id.partner_id.id),
                '|',
                ('product_id', '=', product_lang.id),
                ('product_tmpl_id', '=', product_lang.product_tmpl_id.id)
            ], limit=1)
            if supplier_info:
                name = ""
                if supplier_info.product_code:
                    name = "[%s]" % supplier_info.product_code
                name += " %s" % supplier_info.product_name
                return name
        
        if product_lang.description_sale:
            return product_lang.description_sale
        
        name = ""
        if product_lang.default_code:
            name = "[%s]" % product_lang.default_code 
        name += " %s" % product_lang.name
        return name