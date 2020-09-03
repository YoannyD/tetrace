# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _default_validacion_id(self):
        validacion = self.env['tetrace.validacion_user'].search([
            ('user_id', '=', self.env.user.id),
            ('validacion_id', '!=', False)
        ], limit=1)
        if validacion:
            return validacion.id
        return None

    def _default_validation_user_ids(self):
        return self.env['tetrace.validacion_user'].search([
            ('user_id', '=', self.env.user.id),
            ('validacion_id', '!=', False)
        ]).ids

    validation_user_ids = fields.Many2many('tetrace.validacion_user',
                                           default=lambda self: self._default_validation_user_ids())
    validacion_id = fields.Many2one('tetrace.validacion_user', string="Validación",
                                    default=lambda self: self._default_validacion_id())


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = ""
        if product_lang.description_purchase:
            return product_lang.description_purchase
        return name
