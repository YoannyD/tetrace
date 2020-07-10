# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    secuencia_default_code = fields.Integer('Secuencia Ref. Interna')

    def create(self, vals):
        if not vals.get('default_code'):
            secuencia, default_code = self.generar_default_code()
            vals.update({
                'default_code': default_code,
                'secuencia_default_code': secuencia,
            })

        return super(ProductTemplate, self).create(vals)

    def generar_default_code(self):
        self.ensure_one()
        tipo = ''
        if self.type == 'consu':
            tipo = "C"
        elif self.type == 'service':
            tipo = "S"
        elif self.type == 'product':
            tipo = "S"

        categoria = self.categ_id.name if self.categ_id else None

        ultimo_producto = self.search([('secuencia_default_code', '!=', False)],
                                      order="secuencia_default_code desc", limit=1)
        if ultimo_producto:
            caracteres = len(str(ultimo_producto.secuencia_default_code))
            secuencia = ultimo_producto.secuencia_default_code
            for num in range(1, (5-caracteres)):
                secuencia = "0%s" % secuencia
        else:
            secuencia = "00001"

        code = "%s-%s-%s" % (tipo, categoria, secuencia)
        return secuencia, code

