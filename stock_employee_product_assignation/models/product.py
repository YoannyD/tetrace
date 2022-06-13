# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    assignation_request_ids = fields.One2many('stock.product.assignation.request', 'product_id',
                                              string='Assignation requests')
    can_be_returned = fields.Boolean(string='Can be returned')
