# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductAssignationRequest(models.Model):
    _name = 'stock.product.assignation.request'
    _description = 'Stock Product Assignation Request'

    name = fields.Char(string='S/N')
    date = fields.Date(string='Date', default=fields.Date.today())
    project_id = fields.Many2one('project.project', string='Project')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Integer(string='Quantity')
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], string='State', default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    picking_id = fields.Many2one('stock.picking', string='Picking')
    assignation_ids = fields.One2many('stock.product.assignation', 'request_id', string='Assignations')

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('stock.assignation.request')
        return super(ProductAssignationRequest, self).create(values)

    def action_approved(self):
        for record in self:
            record.state = 'approved'
            picking = self.env['stock.picking'].create(record._prepare_picking())
            picking.action_confirm()
            picking.action_assign()
            record.write({
                'state': 'approved',
                'picking_id': picking.id,
                'assignation_ids': [(0, 0, {
                    'move_line_id': line.id
                }) for line in picking.move_line_ids]
            })

    def _prepare_picking(self):
        self.ensure_one()
        location_destiny = self.env.ref('stock_employee_product_assignation.stock_location_employee_assignation')
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        return {
            'picking_type_id': picking_type.id or None,
            'location_id': picking_type.default_location_src_id.id or None,
            'location_dest_id': location_destiny.id or None,
            'scheduled_date': self.date,
            'origin': self.name,
            'move_ids_without_package': [(0, 0, {
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'product_uom_qty': self.quantity
            })]
        }

    def action_open_assignations(self):
        self.ensure_one()
        action = self.env.ref('stock_employee_product_assignation.action_product_assignation').read()[0]
        ctx = self.env.context.copy()
        ctx.update({
            'create': 0,
            'delete': 0
        })
        action['domain'] = [('request_id', '=', self.id)]
        action['context'] = ctx
        return action


class ProductAssignation(models.Model):
    _name = 'stock.product.assignation'
    _description = 'Stock Product Assignation for Employees'

    request_id = fields.Many2one('stock.product.assignation.request', string='Assignation request', required=True)
    start_date = fields.Date(string='Start date', default=fields.Date.today())
    end_date = fields.Date(string='End date')
    move_line_id = fields.Many2one('stock.move.line', string='Stock move line')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    product_id = fields.Many2one('product.product', related='move_line_id.product_id', store=True)
    observations = fields.Text(string='Observations')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
