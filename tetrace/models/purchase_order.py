# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

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
    sale_order_ids = fields.Many2many('sale.order', compute="_compute_sale_order_ids", string="Pedidos de Venta")
    sale_order_count = fields.Integer("Nº Pedidos de venta", compute="_compute_sale_order_ids")

    @api.depends('origin')
    def _compute_sale_order_ids(self):
        for r in self:
            if r.origin:
                order_ids = []
                for o in r.origin.replace(" ", "").split(","):
                    order = self.env['sale.order'].search([('name', '=', o)], limit=1)
                    if order:
                        order_ids.append(order.id)

                r.update({
                    'sale_order_ids': [(6, 0, order_ids)],
                    'sale_order_count': len(order_ids),
                })
            else:
                r.update({
                    'sale_order_ids': None,
                    'sale_order_count': 0,
                })
    
    @api.depends("amount_untaxed", "date_order")
    def _compute_importe_validacion_euros(self):
        for r in self:
            rate = 0
            if r.date_order:
                euro = self.env['res.currency.rate'].search([
                    ('company_id', '=', 1),
                    ('currency_id', '=', r.currency_id.id),
                    ('name', '<=', r.date_order.strftime('%Y-%m-%d'))
                ], limit = 1)
                if euro:
                    rate = 1/euro.rate
            importe_original = r.amount_untaxed
            r.update({'importe_validacion_euros': importe_original * rate})
            # Si no tasa para Euro el importe_validacion_euros sera igual a 0
            
    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        res.actualizar_cuenta_activo()
        return res
    
    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        self.actualizar_cuenta_activo()
        return res
        
    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        result['context']['default_validacion_id'] = self.validacion_id.id
        result['context']['default_tipo_proyecto_id'] = self.tipo_proyecto_id.id
        return result
    
    def action_view_sale_orders(self):
        action = {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }
        if len(self.sale_order_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.sale_order_ids[0].id,
            })
        else:
            action.update({
                'name': _('Sources Sale Orders %s' % self.name),
                'domain': [('id', 'in', self.sale_order_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action
        
    def actualizar_cuenta_activo(self):
        for r in self:
            if r.cuenta_activo:
                r.order_line.write({'cuenta_activo': True})
                
    @api.model
    def _get_under_validation_exceptions(self):
        res = super(PurchaseOrder, self)._get_under_validation_exceptions()
        res += ["origin", "cuenta_activo"]
        return res
