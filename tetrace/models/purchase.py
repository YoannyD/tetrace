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
    
    account_analytic_id = fields.Many2one(related="order_line.account_analytic_id")
    validacion_id = fields.Many2one('tetrace.validacion_user', string="Validación",
                                    default=lambda self: self._default_validacion_id())
    validacion_baremo = fields.Boolean(related="validacion_id.validacion_id.baremo")
    baremo = fields.Boolean("Fuera Baremo")
    importe_validacion_euros = fields.Monetary("Importe validación en euros", store=True,
                                               compute="_compute_importe_validacion_euros")
    tipo_proyecto_id = fields.Many2one("tetrace.tipo_proyecto", string="Tipo proyecto")
    cuenta_activo = fields.Boolean('Activo')
    
    @api.depends("amount_untaxed", "date_order")
    def _compute_importe_validacion_euros(self):
        for r in self:
            rate = 0
            if r.date_order:
                euro = self.env['res.currency.rate'].search([
                    ('company_id', '=', r.company_id.id),
                    ('currency_id', '=', 1),
                    ('name', '<=', r.date_order.strftime('%Y-%m-%d'))
                ], limit = 1)
                if euro:
                    rate = euro.rate
            importe_original = r.amount_untaxed
            r.update({'importe_validacion_euros': importe_original * rate})
            # Si no tasa para Euro el importe_validacion_euros sera igual a 0

    @api.model
    def _get_under_validation_exceptions(self):
        res = super(PurchaseOrder, self)._get_under_validation_exceptions()
#         res += ["supplier_partner_bank_id", "payment_term_id"]
        return res
            
    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        res.actualizar_cuenta_activo()
        return res
    
    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        self.actualizar_cuenta_activo()
        return res
        
    def actualizar_cuenta_activo(self):
        for r in self:
            if r.cuenta_activo:
                r.order_line.write({'cuenta_activo': True})


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
    
    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = ""
        if product_lang.description_purchase:
            return product_lang.description_purchase
        return name
    
    def _prepare_account_move_line(self, move):
        self.ensure_one()
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if self.cuenta_activo and self.product_id.categ_id:
            res.update({'account_id': self.product_id.categ_id.account_activo_id.id})
        return res
