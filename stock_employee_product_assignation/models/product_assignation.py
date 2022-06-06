# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductAssignation(models.Model):
    _name = 'stock.product.assignation'
    _description = 'Stock Product Assignation for Employees'

    start_date = fields.Date(string='Start date', default=fields.Date.today())
    end_date = fields.Date(string='End date')
    project_id = fields.Many2one('project.project', string='Project')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='S/N')
    warehouse_location = fields.Boolean(string='Warehouse location?')
    observations = fields.Text(string='Observations')
    company_id = fields.Many2one('res.company', string='Company')
