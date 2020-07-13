# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = "product.category"

    referencia = fields.Char('Referencia')

    def write(self, vals):
        res = super(ProductCategory, self).write(vals)
        if 'referencia' in vals:
            product_tmpls = self.env['product.template'].search([
                ('categ_id', 'in', self.ids),
                ('secuencia_default_code', '!=', False)
            ])
            if product_tmpls:
                for product in product_tmpls:
                    secuencia, default_code = product.generar_default_code(True)
                    product.write({'default_code': default_code})
        return res
