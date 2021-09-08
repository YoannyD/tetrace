# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = "product.category"

    referencia = fields.Char('Referencia')
    account_activo_id = fields.Many2one('account.account', string="Cuenta activo", company_dependent=True,
                                        domain="['&', ('deprecated', '=', False), ('company_id', '=', current_company_id)]",)
    categoria_equipo_id = fields.Many2one('maintenance.equipment.category', string="Categoría equipo")

    def write(self, vals):
        res = super(ProductCategory, self).write(vals)
        if 'referencia' in vals:
            product_tmpls = self.env['product.template'].search([('categ_id', 'in', self.ids)])
            if product_tmpls:
                for product in product_tmpls:
                    secuencia, default_code = product.generar_default_code(True)
                    product.write({
                        'default_code': default_code,
                        'secuencia_default_code': secuencia
                    })
        return res
