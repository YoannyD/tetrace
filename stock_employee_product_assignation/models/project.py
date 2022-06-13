# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Project(models.Model):
    _inherit = 'project.project'

    assignation_ids = fields.One2many('stock.product.assignation.request', 'project_id', string='Equipments')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    assignation = fields.Boolean("Asignaciones de equipos")
    assignation_ids = fields.One2many('stock.product.assignation', 'task_id', 'Assignations')
    assignation_count = fields.Integer("Nª Asignaciones", compute="_compute_assignation_count")

    def _compute_assignation_count(self):
        self.assignation_count = len(self.assignation_ids)

    def action_open_assignations(self):
        self.ensure_one()
        action = self.env.ref('stock_employee_product_assignation.action_product_assignation').read()[0]
        ctx = self.env.context.copy()
        ctx.update({
            'create': 0,
            'delete': 0
        })
        action['domain'] = [('id', 'in', self.assignation_ids.ids), ('active', 'in' [False, True])]
        action['context'] = ctx
        return action
