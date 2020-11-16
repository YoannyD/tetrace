# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Estado(models.Model):
    _name = 'tetrace.project_state'
    _description = "Estados"
    _order = "sequence,name"

    sequence = fields.Integer('Secuencia')
    name = fields.Char('Nombre', required=True)
    project_ids = fields.One2many('project.project', 'estado_id')


class Project(models.Model):
    _inherit = 'project.project'

    def _default_estado_id(self):
        return self.env['tetrace.project_state'].search([], limit=1).id

    descripcion = fields.Text("Descripción")
    estado_id = fields.Many2one('tetrace.project_state', string='Estado', ondelete='restrict', tracking=True,
                                index=True, group_expand='_read_group_estado_ids',
                                copy=False, default=lambda self: self._default_estado_id())
    product_tmpl_diseno_ids = fields.One2many("product.template", "project_template_diseno_id")
    color = fields.Integer(related="sale_order_id.tipo_servicio_id.color")
    partner_latitude = fields.Float('Geo Latitude', digits=(16, 5))
    partner_longitude = fields.Float('Geo Longitude', digits=(16, 5))
    partner_geo_id = fields.Many2one("res.partner", string="Geolocalización")
                
    def _table_get_empty_so_lines(self):
        """ get the Sale Order Lines having no timesheet but having generated a task or a project """
        so_lines = self.sudo() \
            .mapped('sale_line_id.order_id.order_line') \
            .filtered(lambda sol: sol.is_service and sol.product_id.service_policy == 'delivered_timesheet' and not sol.is_expense and not sol.is_downpayment)
        # include the service SO line of SO sharing the same project
        sale_order = self.env['sale.order'].search([('project_id', 'in', self.ids)])
        return set(so_lines.ids) | set(sale_order.mapped('order_line').filtered(lambda sol: sol.is_service and sol.product_id.service_policy == 'delivered_timesheet' and not sol.is_expense).ids), set(
            so_lines.mapped('order_id').ids) | set(sale_order.ids)

    def _table_get_line_values(self):
        result = super(Project, self)._table_get_line_values()

        sales_group = {}
        timesheet_forecast_table_rows = []
        for row in result['rows']:
            new_row = row
            if row[0]['res_id'] and row[0]['res_model'] == 'sale.order.line':
                sale_line_id = self.env['sale.order.line'].sudo().browse(row[0]['res_id'])
                if sale_line_id:
                    new_row[6] = sale_line_id.qty_invoiced
                    new_row[7] = sale_line_id.qty_delivered - sale_line_id.qty_invoiced

                    key = str(sale_line_id.order_id.id)
                    if key not in sales_group:
                        sales_group.update({key: {'facturado': 0, 'restante': 0}})
                    sales_group[key]['facturado'] += new_row[6]
                    sales_group[key]['restante'] += new_row[7]

            timesheet_forecast_table_rows.append(new_row)

        table_rows = []
        for row in timesheet_forecast_table_rows:
            new_row = row
            if row[0]['res_id'] and str(row[0]['res_id']) in sales_group and row[0]['res_model'] == 'sale.order':
                key = str(row[0]['res_id'])
                new_row[6] = sales_group[key]['facturado']
                new_row[7] = sales_group[key]['restante']
            table_rows.append(new_row)

        return {
            'header': result['header'],
            'rows': table_rows
        }
    
    @api.model
    def _read_group_estado_ids(self, estados, domain, order):
        return self.env['tetrace.project_state'].search([])
    
    def view_responsables_tree(self):
        self.ensure_one()
        ctx = dict(self._context)
        ctx.update({'search_default_project_id': self.id})
        ctx.update({'search_default_user': True})
        action = self.env['ir.actions.act_window'].for_xml_id('project', 'act_project_project_2_project_task_all')
        action['view_mode'] = "tree,kanban,form,calendar,pivot,graph,activity"
        action['views'] = [(False, 'tree'), (False, 'kanban'), (False, 'form'), (False, 'calendar'), (False, 'pivot'), (False, 'graph'), (False, 'activity'), (False, 'gantt'), (False, 'map')]
        return dict(action, context=ctx)
    
    def create(self, vals):
        res = super(Project, self).write(vals)
        res.actualizar_geo_partner()
        return res
    
    def write(self, vals):
        res = super(Project, self).write(vals)
        if 'name' in vals or 'partner_latitude' in vals or 'partner_longitude' in vals:
            self.actualizar_geo_partner()
        return res
    
    def actualizar_geo_partner(self):
        for r in self:
            values = {
                'name': "Geolocalización %s" % r.name,
                'partner_latitude': r.partner_latitude,
                'partner_longitude': r.partner_longitude,
            }
            
            if not r.partner_geo_id:
                values.update({'project_geo_ids': [(6, 0, [r.id])]})
                self.env['res.partner'].with_context(no_actualizar=True).create(values)
            else:
                r.partner_geo_id.with_context(no_actualizar=True).write(values)
                
    def view_tecnicos_tree(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('tetrace', 'open_view_project_contract')
        action.update({'domain': [('project_id', '=', self.id)]})
        return action
    
    def view_procesos_seleccion_tree(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('tetrace', 'open_view_project_applicant')
        action.update({'domain': [('project_id', '=', self.id)]})
        return action
    
    def action_view_project(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('project', 'open_view_project_all')
        view_form_id = self.env.ref('project.edit_project').id
        action.update({
            'views': [(view_form_id, 'form')],
            'view_mode': 'form,kanban',
            'res_id': self.id
        })
        return action

    
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    tarea_seleccion = fields.Boolean("Tarea Selección")
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    applicant_ids = fields.Many2many('hr.applicant', 'task_applicant_rel', 'task_id', 'applicant_id')
    contract_ids = fields.Many2many('hr.contract', 'task_contract_rel', 'task_id', 'contract_id')
    

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    bloquear_imputar_tiempos = fields.Boolean('Bloquear imputación de tiempos')
