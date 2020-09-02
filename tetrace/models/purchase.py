# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_user_id = fields.Many2one(compute="_compute_partner_user_id", store=True)
    validacion_id = fields.Many2one('tetrace.validacion', string="Validación")

    @api.depends('partner_id')
    def _compute_partner_user_id(self):
        for r in self:
            if r.partner_id and r.partner_id.user_ids:
                r.partner_user_id = r.partner_id.user_ids[0].id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for r in self:
            if r.partner_user_id and r.partner_user_id.validacion_user_ids:
                r.validacion_id = r.partner_user_id.validacion_user_ids[0].validacion_id.id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = ""
        if product_lang.description_purchase:
            return product_lang.description_purchase
        return name
