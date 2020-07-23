# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []

        if self.env.context.get('invoice_type') in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'] and \
            self.env.context.get('journal_id'):
            journal = self.env['account.journal'].search([
                ('id', '=', self.env.context.get('journal_id')),
                ('code', '=', 'INVE')
            ], limit=1)

            if journal:
                args += [('intrastat_id', '!=', False)]

        return super(Product, self)._name_search(name, args, operator, limit, name_get_uid)

    def get_product_multiline_description_sale(self):
        name = ''
        if self.description_sale:
            name += '\n' + self.description_sale
        return name
