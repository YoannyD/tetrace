# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import tempfile
import binascii
import xlrd
import io

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ImportarProductoPV(models.TransientModel):
    _name = 'tetrace.importar_producto_pv'
    _description = "Importar productos en pedidos de venta"
    
    order_id = fields.Many2one("sale.order", string="Pedido Venta", ondelete="cascade")
    file = fields.Binary('File')
    
    def action_importar(self):
        self.ensure_one()
        if not self.order_id.partner_id:
            return {'type': 'ir.actions.act_window_close'}
        
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
            
            if not line[0]:
                continue
            
            refs_producto = self.env["product.customerinfo"].search([
                ('company_id', '=', self.order_id.company_id.id),
                ('product_code', '=', line[0])
            ])
            
            ref_producto = None
            for ref in refs_producto:
                if not ref_producto:
                    ref_producto = ref
                    continue
                    
                if ref.name.id == self.order_id.partner_id.id:
                    ref_producto = ref
                    break

            product = False
            if ref_producto:
                if ref_producto.product_id:
                    product = ref_producto.product_id
                elif ref_producto.product_tmpl_id:
                    product = ref_producto.product_tmpl_id.product_variant_id
              
            try:
                cantidad = float(line[1])
            except:
                cantidad = 0.0
            
            if product:
                self.env['sale.order.line'].create({
                    'order_id': self.order_id.id,
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': cantidad,
                    'price_unit': ref_producto.price,
                    'name': ref_producto.product_name
                })
            else:
                RefProducto = self.env["tetrace.ref_producto"]
                ref_producto = RefProducto.search([
                    ('order_id', '=', self.order_id.id),
                    ('name', '=', line[0])
                ], limit=1)
                if not ref_producto:
                    RefProducto.create({
                        'order_id': self.order_id.id,
                        'name': line[0],
                        'cantidad': cantidad
                    })
                else:
                    ref_producto.write({'cantidad': cantidad})

        return {'type': 'ir.actions.act_window_close'}
        
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