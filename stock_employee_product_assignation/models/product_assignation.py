# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class ProductAssignationRequest(models.Model):
    _name = 'stock.product.assignation.request'
    _description = 'Stock Product Assignation Request'

    name = fields.Char(string='Assignation Number')
    date = fields.Date(string='Date', default=fields.Date.today())
    project_id = fields.Many2one('project.project', string='Project')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Integer(string='Quantity')
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], string='State', default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    picking_id = fields.Many2one('stock.picking', string='Picking')
    assignation_ids = fields.One2many('stock.product.assignation', 'request_id', string='Assignations')
    color = fields.Integer(string='Color Index', default=1)
    observations = fields.Text('Observations')
    task_id = fields.Many2one('project.task', 'Task', compute='_compute_task')

    def _compute_task(self):
        task = False
        if self.project_id:
            tasks = self.env['project.task'].search([
                ('project_id', '=', self.project_id.id),
                ('activada', 'in', [True, False]),
                ('assignation', '=', True)
            ])
            if tasks:
                task = tasks[0].id
        self.task_id = task

    def unlink(self):
        for assignation in self:
            if assignation.state == 'approved':
                raise UserError(_("No puede eliminar una solicitud aprobada"))
        return super(ProductAssignationRequest, self).unlink()

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('stock.assignation.request')
        values['state'] = 'draft'
        values['company_id'] = self.env.company.id
        return super(ProductAssignationRequest, self).create(values)

    def create_assignation_activity(self):
        for record in self:
            summary = _('Necesidad de equipo para el proyecto %s' % record.project_id.name)

            tasks = self.env['project.task'].search([
                ('project_id', '=', record.project_id.id),
                ('activada', 'in', [True, False]),
                ('assignation', '=', True)
            ])
            if tasks:
                tasks.create_activity(summary)

    def action_approved(self):
        for record in self:
            picking = self.env['stock.picking'].create(record._prepare_picking())
            picking.action_confirm()
            picking.action_assign()
            record.write({
                'state': 'approved',
                'color': 10,
                'picking_id': picking.id,
                'assignation_ids': [(0, 0, {
                    'move_line_id': line.id
                }) for line in picking.move_line_ids]
            })
            record.create_assignation_activity()

    def _prepare_picking(self):
        self.ensure_one()
        location_destiny = self.env.ref('stock_employee_product_assignation.stock_location_employee_assignation')
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        procure_method = 'make_to_stock'
        if (self.product_id.virtual_available + self.product_id.qty_available) < self.quantity:
            procure_method = 'make_to_order'
        return {
            'picking_type_id': picking_type.id or None,
            'location_id': picking_type.default_location_src_id.id or None,
            'location_dest_id': location_destiny.id or None,
            'scheduled_date': self.date,
            'origin': self.name,
            'assignation_request_id': self.id,
            'move_ids_without_package': [(0, 0, {
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'product_uom_qty': self.quantity,
                'procure_method': procure_method,
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

    def action_view_picking(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        # override the context to get rid of the default filtering on operation type
        pick_ids = self.mapped('picking_id')
        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pick_ids.id
        return result


class ProductAssignation(models.Model):
    _name = 'stock.product.assignation'
    _description = 'Stock Product Assignation for Employees'
    _rec_name = 'code'

    request_id = fields.Many2one('stock.product.assignation.request', string='Assignation request', required=True)
    start_date = fields.Date(string='Start date', default=fields.Date.today())
    end_date = fields.Date(string='End date')
    move_line_id = fields.Many2one('stock.move.line', string='Stock move line')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    product_id = fields.Many2one('product.product', related='move_line_id.product_id', store=True)
    observations = fields.Text(string='Observations')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    code = fields.Char('Serial Number')
    task_id = fields.Many2one('project.task', 'Task')
    code_readonly = fields.Boolean('Code Readonly', default=False)
    assignation_return = fields.Boolean('Assignation return', default=False)
    return_move_line_id = fields.Many2one('stock.move.line', string='Return Stock move line')

    def _prepare_picking(self):
        self.ensure_one()
        location_origin = self.env.ref('stock_employee_product_assignation.stock_location_employee_assignation')
        if self.product_id.can_be_returned:
            location_destiny = self.move_line_id.location_id
        else:
            location_destiny = self.product_id.property_stock_inventory
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        return {
            'picking_type_id': picking_type.id or None,
            'location_dest_id': location_destiny.id or None,
            'location_id': location_origin.id or None,
            'scheduled_date': fields.Date.context_today(self),
            'origin': self.request_id.name,
            'assignation_request_id': self.request_id.id,
            'move_ids_without_package': [(0, 0, {
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'product_uom_qty': 1,
            })]
        }

    def cron_return_out_date_assignation(self):
        out_date_assignations = self.env['stock.product.assignation'].search([
            ('assignation_return', '=', False),
            ('end_date', '!=', False),
            ('end_date', '<=', fields.Date.today())
        ])
        out_date_assignations.action_return()

    def action_return(self):
        for record in self:
            picking = self.env['stock.picking'].create(record._prepare_picking())
            picking.action_confirm()
            picking.action_assign()
            for line in picking.move_ids_without_package.move_line_ids:
                line.qty_done = 1
                line.lot_id = record.move_line_id.lot_id.id or None
                record.return_move_line_id = line.id
            picking.button_validate()
            record.assignation_return = True
