# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    assignation_ids = fields.One2many('stock.product.assignation', 'product_id', string='Assignations')
