# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_user_id = fields.Many2one('res.users', compute="_compute_partner_user_id", store=True)
    validation_user_ids = fields.Many2many('tetrace.validacion_user')
    validacion_id = fields.Many2one('tetrace.validacion_user', string="Validación")

    @api.depends('partner_id')
    def _compute_partner_user_id(self):
        for r in self:
            user_id = False
            if r.partner_id:
                user = self.env['res.users'].search([('partner_id', '=', r.partner_id.id)], limit=1)
                if user:
                    user_id = user.id
            r.partner_user_id = user_id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for r in self:
            if r.partner_user_id and r.partner_user_id.validacion_user_ids:
                validacion_ids = []
                validacion_id = None
                for vu in r.partner_user_id.validacion_user_ids:
                    validacion_id = vu.id
                    validacion_ids.append(vu.id)

                r.update({
                    'validation_user_ids': [(6, 0, validacion_ids)],
                    'validacion_id': validacion_id
                })


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = ""
        if product_lang.description_purchase:
            return product_lang.description_purchase
        return name
