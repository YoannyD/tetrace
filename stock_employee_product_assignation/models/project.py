# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Project(models.Model):
    _inherit = 'project.project'

    assignation_ids = fields.One2many('stock.product.assignation', 'project_id', string='Equipments')
