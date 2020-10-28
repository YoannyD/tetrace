# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tetrace_account_id = fields.Many2one("tetrace.account", string="Cuenta Tetrace", company_dependent=False,
                                         compute="_compute_tetrace_account_id", store=True)
    asiento_anticipo_id = fields.Many2one(related="move_id.asiento_anticipo_id")
    asiento_anticipo_fecha_vencimiento = fields.Date("Fecha vencimiento anticipo",
                                                     compute="_compute_asiento_anticipo_fecha_vencimiento")
    confirmado = fields.Boolean('Confirmado')
    account_move_fecha_servicio = fields.Date(related="move_id.fecha_servicio")
    
    @api.constrains("analytic_account_id", "account_id", "debit", "credit")	
    def _check_analytic_required(self):
        #Evitamos la restricción de la cuenta/etiqueta analitica si se trata apuntes sobre el diario de diferencia
        #de cambio de la compañía
        if self.move_id.journal_id.id != self.env.company.currency_exchange_journal_id.id:	
            res = super(AccountMoveLine, self)._check_analytic_required()		
            return res
        else:
            return None  
    
    @api.depends("account_id.tetrace_account_id")
    def _compute_tetrace_account_id(self):
        for r in self:
            r.tetrace_account_id = r.account_id.tetrace_account_id.id if r.account_id.tetrace_account_id else None

    def _compute_asiento_anticipo_fecha_vencimiento(self):
        for r in self:
            fecha_vencimiento = None
            if r.asiento_anticipo_id:
                for line in r.asiento_anticipo_id.line_ids:
                    if line.date_maturity and line.account_id and line.account_id.group_id and \
                        line.account_id.group_id.code_prefix == '5200':
                        fecha_vencimiento = line.date_maturity
                        break
            r.asiento_anticipo_fecha_vencimiento = fecha_vencimiento

    def _sale_create_reinvoice_sale_line(self):
        sale_order_map = self._sale_determine_order()

        sale_line_values_to_create = []  # the list of creation values of sale line to create.
        existing_sale_line_cache = {}  # in the sales_price-delivery case, we can reuse the same sale line. This cache will avoid doing a search each time the case happen
        # `map_move_sale_line` is map where
        #   - key is the move line identifier
        #   - value is either a sale.order.line record (existing case), or an integer representing the index of the sale line to create in
        #     the `sale_line_values_to_create` (not existing case, which will happen more often than the first one).
        map_move_sale_line = {}

        for move_line in self:
            sale_order = sale_order_map.get(move_line.id)

            # no reinvoice as no sales order was found
            if not sale_order:
                continue

            # raise if the sale order is not currenlty open
            if sale_order.state != 'sale':
                message_unconfirmed = _('The Sales Order %s linked to the Analytic Account %s must be validated before registering expenses.')
                messages = {
                    'draft': message_unconfirmed,
                    'sent': message_unconfirmed,
                    'done': _('The Sales Order %s linked to the Analytic Account %s is currently locked. You cannot register an expense on a locked Sales Order. Please create a new SO linked to this Analytic Account.'),
                    'cancel': _('The Sales Order %s linked to the Analytic Account %s is cancelled. You cannot register an expense on a cancelled Sales Order.'),
                }
                raise UserError(messages[sale_order.state] % (sale_order.name, sale_order.analytic_account_id.name))

            price = move_line._sale_get_invoice_price(sale_order)

            # find the existing sale.line or keep its creation values to process this in batch
            sale_line = None
            if move_line.product_id.expense_policy == 'sales_price' and (move_line.product_id.invoice_policy == 'delivery' or move_line.product_id.service_policy == 'delivered_manual'):  # for those case only, we can try to reuse one
                map_entry_key = (sale_order.id, move_line.product_id.id, price)  # cache entry to limit the call to search
                sale_line = existing_sale_line_cache.get(map_entry_key)
                if sale_line:  # already search, so reuse it. sale_line can be sale.order.line record or index of a "to create values" in `sale_line_values_to_create`
                    map_move_sale_line[move_line.id] = sale_line
                    existing_sale_line_cache[map_entry_key] = sale_line
                else:  # search for existing sale line
                    sale_line = self.env['sale.order.line'].search([
                        ('order_id', '=', sale_order.id),
                        ('product_id', '=', move_line.product_id.id)
                    ], limit=1)
                    if sale_line:  # found existing one, so keep the browse record
                        sale_line.update({'is_expense': True})
                        map_move_sale_line[move_line.id] = existing_sale_line_cache[map_entry_key] = sale_line
                    else:  # should be create, so use the index of creation values instead of browse record
                        # save value to create it
                        sale_line_values_to_create.append(move_line._sale_prepare_sale_line_values(sale_order, price))
                        # store it in the cache of existing ones
                        existing_sale_line_cache[map_entry_key] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line
                        # store it in the map_move_sale_line map
                        map_move_sale_line[move_line.id] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line

            else:  # save its value to create it anyway
                sale_line_values_to_create.append(move_line._sale_prepare_sale_line_values(sale_order, price))
                map_move_sale_line[move_line.id] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line

        # create the sale lines in batch
        new_sale_lines = self.env['sale.order.line'].create(sale_line_values_to_create)

        # build result map by replacing index with newly created record of sale.order.line
        result = {}
        for move_line_id, unknown_sale_line in map_move_sale_line.items():
            if isinstance(unknown_sale_line, int):  # index of newly created sale line
                result[move_line_id] = new_sale_lines[unknown_sale_line]
            elif isinstance(unknown_sale_line, models.BaseModel):  # already record of sale.order.line
                result[move_line_id] = unknown_sale_line
        return result

    def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id

        name = ''
        if self.journal_id.type == 'sale':
            if product.description_sale:
                name = product.description_sale
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                name =  product.description_purchase

        if not name and product.partner_ref:
            name = product.partner_ref

        return name
    
    def _prepare_analytic_line(self):
        res = super(AccountMoveLine, self)._prepare_analytic_line()
        for values in res:
            move_line = self.env['account.move.line'].browse(values['move_id'])
            company_id = self.env.company.id
            if move_line and move_line.move_id and move_line.move_id.company_id:
                company_id = move_line.move_id.company_id.id
            elif move_line:
                company_id = move_line.analytic_account_id.company_id.id
                
            values.update({'company_id': company_id})
        return res
            
