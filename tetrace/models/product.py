# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []

        if self.env.context.get('invoice_type') in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'] and \
            self.env.context.get('journal_id'):
            journal = self.env['account.journal'].search([
                ('id', '=', self.env.context.get('journal_id')),
                ('code', '=', 'INVE')
            ], limit=1)

            if journal:
                args += [('intrastat_id', '!=', False)]

        return super(Product, self)._name_search(name, args, operator, limit, name_get_uid)
    
    @api.model
    def create(self, vals):
        res = super(Product, self).create(vals)
        if not res.default_code:
            secuencia, default_code = res.generar_default_code(False)
            res.write({
                'default_code': default_code,
                'secuencia_default_code': secuencia,
            })
        return res
    
    def write(self, vals):
        res = super(Product, self).write(vals)
        if 'type' in vals or 'categ_id' in vals:
            for r in self:
                secuencia, default_code = r.generar_default_code(True)
                r.write({
                    'default_code': default_code,
                    'secuencia_default_code': secuencia
                })
        return res
    
    def generar_default_code(self, update=False):
        tipo = ''
        if self.type == 'consu':
            tipo = "C"
        elif self.type == 'service':
            tipo = "S"
        elif self.type == 'product':
            tipo = "P"

        categoria = self.categ_id.referencia if self.categ_id and self.categ_id.referencia else '00'

        def secuencia_str(code):
            caracteres = len(str(code))
            secuencia = code + 1
            for num in range(0, (5 - caracteres)):
                secuencia = "0%s" % secuencia
            return secuencia

        if update and self.secuencia_default_code:
            secuencia = secuencia_str(self.secuencia_default_code)
            secuencia_int = self.secuencia_default_code
        else:
            ultimo_producto = self.search([('secuencia_default_code', '!=', False)],
                                          order="secuencia_default_code desc", limit=1)
            if ultimo_producto:
                secuencia = secuencia_str(ultimo_producto.secuencia_default_code)
                secuencia_int = ultimo_producto.secuencia_default_code
            else:
                secuencia = "00001"
                secuencia_int = 1
            secuencia_int = secuencia_int + 1

        code = "%s-%s-%s" % (tipo, categoria, secuencia)
        return secuencia_int, code
    
    def get_code_supplier_info(self, partner):
        self.ensure_one()
        supplier_info = self.env["product.supplierinfo"].search([
            ('name', '=', partner.id),
            ('product_code', '!=', False),
            '|',
            ('product_id', '=', self.id),
            ('product_tmpl_id', '=', self.product_tmpl_id.id)
        ], limit=1)
        
        return supplier_info.product_code if supplier_info else None
    
    def get_code_customer_info(self, partner):
        self.ensure_one()
        customer_info = self.env["product.customerinfo"].search([
            ('name', '=', partner.id),
            ('product_code', '!=', False),
            '|',
            ('product_id', '=', self.id),
            ('product_tmpl_id', '=', self.product_tmpl_id.id)
        ], limit=1)
        
        return customer_info.product_code if customer_info else None
    
    def get_name_supplier_info(self, partner):
        self.ensure_one()
        supplier_info = self.env["product.supplierinfo"].search([
            ('product_name', '!=', False),
            ('name', '=', partner.id),
            '|',
            ('product_id', '=', self.id),
            ('product_tmpl_id', '=', self.product_tmpl_id.id)
        ], limit=1)
        return supplier_info.product_name if supplier_info else None
    
    def get_name_customer_info(self, partner):
        self.ensure_one()
        customer_info = self.env["product.customerinfo"].search([
            ('product_name', '!=', False),
            ('name', '=', partner.id),
            '|',
            ('product_id', '=', self.id),
            ('product_tmpl_id', '=', self.product_tmpl_id.id)
        ], limit=1)
        return customer_info.product_name if customer_info else None
    
    def get_product_multiline_description_sale(self):
        if self.env.context.get('partner_id'):
            customer_info = self.env["product.customerinfo"].search([
                ('product_name', '!=', False),
                ('name', '=', self.env.context.get('partner_id')),
                '|',
                ('product_id', '=', self.id),
                ('product_tmpl_id', '=', self.product_tmpl_id.id)
            ], limit=1)
            if customer_info:
                name = ""
                if customer_info.product_code:
                    name = "[%s]" % customer_info.product_code
                name += " %s" % customer_info.product_name
                return name
        
        if self.description_sale:
            return self.description_sale
        
        name = ""
        if self.default_code:
            name = "[%s]" % self.default_code 
        name += " %s" % self.name
        return name
