# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    assignation_ids = fields.One2many('stock.product.assignation', 'employee_id', string='Equipments')
    assignation_count = fields.Integer(compute='_compute_assignation_count', string='Equipments')

    def _compute_assignation_count(self):
        for record in self:
            record.assignation_count = len(record.assignation_ids)

    def action_open_equipments(self):
        self.ensure_one()
        action = self.env.ref('stock_employee_product_assignation.action_product_assignation').read()[0]
        ctx = self.env.context.copy()
        ctx.update({
            'default_employee_id': self.id
        })
        action['view_mode'] = 'tree,form'
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = ctx
        return action
