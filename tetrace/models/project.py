# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

OPCIONES_DESACTIVACION = [
    ('viaje', 'Viaje'),
    ('baja', 'Baja'),
    ('informatica', 'Informática'),
    ('equipos', 'Equipos'),
    ('reubicacion', 'Reubicación'),
    ('facturacion', 'Facturación'),
]


class Estado(models.Model):
    _name = 'tetrace.project_state'
    _description = "Estados"
    _order = "sequence,name"

    sequence = fields.Integer('Secuencia')
    name = fields.Char('Nombre', required=True)
    project_ids = fields.One2many('project.project', 'estado_id')


class MotivoCancelacion(models.Model):
    _name = 'tetrace.motivo_cancelacion'
    _description = "Motivos cancelación"
    _order = "sequence,name"

    sequence = fields.Integer("Secuencia")
    name = fields.Char('Motivo')
    project_ids = fields.One2many("project.project", "motivo_cancelacion_id")
    
    
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
    url_proyecto = fields.Char("URL proyecto")
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_cancelacion = fields.Date("Fecha cancelación")
    fecha_finalizacion = fields.Date("Fecha finalización")
    motivo_cancelacion_id = fields.Many2one('tetrace.motivo_cancelacion', string="Motivo cancelación")
                
    @api.constrains("fecha_cancelacion", "motivo_cancelacion_id")
    def _check_motivo_cancelacion_id(self):
        for r in self:
            if r.fecha_cancelacion and not r.motivo_cancelacion_id:
                raise ValidationError(_("Si hay fecha de cancelación es olbigatorio indicar el motivo"))
        
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
    
    def view_sale_order_form(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('sale', 'action_quotations_with_onboarding')
        view_form_id = self.env.ref('sale.view_order_form').id
        action.update({
            'views': [(view_form_id, 'form')],
            'view_mode': 'form,tree',
            'res_id': self.sale_order_id.id
        })
        return action
    
    @api.model
    def create(self, vals):
        vals = self.actualizar_vals(vals)
        res = super(Project, self).create(vals)
        res.actualizar_geo_partner()
        res.actualizar_deadline_tareas()
        return res
    
    def write(self, vals):
        res = super(Project, self).write(vals)
        vals = self.actualizar_vals(vals)
        if 'name' in vals or 'partner_latitude' in vals or 'partner_longitude' in vals:
            self.actualizar_geo_partner()
            
        if 'fecha_inicio' in vals:
            self.actualizar_deadline_tareas()
        return res
    
    def actualizar_deadline_tareas(self):
        for r in self:
            if not r.fecha_inicio:
                continue
                
            for task in r.tasks:
                if task.tipo != 'activacion' or task.date_deadline:
                    continue
                
                date_deadline = fields.Date.from_string(r.fecha_inicio) + timedelta(days=task.deadline_inicio)
                task.write({'date_deadline': date_deadline})
    
    @api.model
    def actualizar_vals(self, vals):
        if "estado_id" in vals and vals.get("estado_id") != 4:
            vals.update({"motivo_cancelacion_id": False})
        return vals
    
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
    
    def action_activar_tareas(self):
        self.ensure_one()
        wizard = self.env['tetrace.activar_tarea'].create({"project_id": self.id})
        return wizard.open_wizard()

    def view_analitica_tree(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('analytic', 'account_analytic_line_action')
        action["domain"] = [('account_id', '=', self.analytic_account_id.id)]
        action["context"] = {'search_default_group_date': 1, 'default_account_id': self.analytic_account_id.id}
        return action
    
    
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    @api.model
    def _default_sale_line_id(self):
        return False
    
    tarea_seleccion = fields.Boolean("Tarea Selección")
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    applicant_ids = fields.Many2many('hr.applicant', 'task_applicant_rel', 'task_id', 'applicant_id')
    contract_ids = fields.Many2many('hr.contract', 'task_contract_rel', 'task_id', 'contract_id')
    entrega_ids = fields.One2many('project.task.entrega', 'task_id')
    entrega_total = fields.Float('Total entrega', compute="_compute_entrega_total")
    producto_entrega = fields.Boolean(related="sale_line_id.product_entregado")
    desde_plantilla = fields.Boolean("Creada desde plantilla")
    tipo = fields.Selection([
        ('activacion', 'Activación'), 
        ('desactivacion', 'Desactivacion')
    ], string="Tipo tarea")
    tarea_individual = fields.Boolean("Individual")
    viajes = fields.Boolean("Viajes")
    viaje_ids = fields.One2many("tetrace.viaje", "task_id")
    activada = fields.Boolean("Activada", default=True)
    opciones_desactivacion = fields.Selection(OPCIONES_DESACTIVACION, string="Desactivación")
    sale_line_id = fields.Many2one('sale.order.line', default=_default_sale_line_id)
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    deadline_inicio = fields.Integer("Deadline inicio")
    deadline_fin = fields.Integer("Deadline fin")

    @api.constrains('tarea_individual', 'tarea_seleccion', 'tipo')
    def _check_tipos_tareas(self):
        for r in self:
            if r.tarea_seleccion and not r.tarea_individual:
                raise ValidationError("Si es tarea de selección tiene que ser tarea individual")
    
    @api.depends("entrega_ids.entregado")
    def _compute_entrega_total(self):
        for r in self:
            total = 0
            if not r.desde_plantilla and r.producto_entrega:
                for entrega in r.entrega_ids:
                    total += entrega.entregado
            r.entrega_total = total
            
    @api.onchange('project_id')
    def _onchange_project(self):
        result = super(ProjectTask, self)._onchange_project()
        self.sale_line_id = False
        return result
            
    @api.onchange("tarea_seleccion")
    def _onchange_tarea_seleccion(self):
        for r in self:
            if r.tarea_seleccion:
                r.tarea_individual = True
    
    def write(self, vals):
        entregas = {}
        for r in self:
            entregas.update({
                str(r.id): {
                    'registro': r,
                    'total': r.entrega_total
                }
            })
            
        res = super(ProjectTask, self).write(vals)
        
        for r in self:
            if not r.desde_plantilla and r.producto_entrega and entregas[str(r.id)]['total'] != r.entrega_total:
                r.sale_line_id.write({'qty_delivered': r.entrega_total})
                body = "<strong>Entrega:</strong><br/>Cantidad entregada %s -> %s" % (entregas[str(r.id)]['total'], r.entrega_total)
                r.message_post(body=body, subject="Entrega")
        return res
    
    @api.model
    def _where_calc(self, domain, active_test=True):
        if 'activada' in self._fields and active_test and self._context.get('active_test', True):
            if not any(item[0] == 'activada' for item in domain):
                domain = [('activada', '=', 1)] + domain
        return super(ProjectTask, self)._where_calc(domain, active_test)
    
    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        if self.env.context.get("default_res_model") == 'project.project':
            return
        return super(ProjectTask, self).message_subscribe(partner_ids, channel_ids, subtype_ids)
    
    def message_unsubscribe(self, partner_ids=None, channel_ids=None):
        if not partner_ids and not channel_ids:
            return True
        
        user_pid = self.env.user.partner_id.id
        if not channel_ids and set(partner_ids) == set([user_pid]):
            self.check_access_rights('read')
            self.check_access_rule('read')
        else:
            self.check_access_rights('write')
            self.check_access_rule('write')
            
        self.env['mail.followers'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            '|',
            ('partner_id', 'in', partner_ids or []),
            ('channel_id', 'in', channel_ids or [])
        ]).unlink()
        
    def copy(self, default=None):
        self.ensure_one()
        new_task = super(ProjectTask, self).copy(default)
        if self.message_partner_ids:
            new_task.with_context(add_follower=True).message_subscribe(self.message_partner_ids.ids, [])
            new_task.notificar_asignacion_seguidores()
        return new_task
        
    def notificar_asignacion_seguidores(self):
        view = self.env['ir.ui.view'].browse(self.env['ir.model.data'].xmlid_to_res_id("mail.message_user_assigned"))
        for r in self:
            if not r.message_partner_ids:
                continue
                
            values = {
                'object': r,
                'model_description': r.display_name,
            }
            assignation_msg = view.render(values, engine='ir.qweb', minimal_qcontext=True)
            assignation_msg = self.env['mail.thread']._replace_local_links(assignation_msg)
            r.message_notify(
                subject=_('You have been assigned to %s') % r.display_name,
                body=assignation_msg,
                partner_ids=r.message_partner_ids.ids,
                record_name=r.display_name,
                email_layout_xmlid='mail.mail_notification_light',
                model_description=r.name,
            )


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    bloquear_imputar_tiempos = fields.Boolean('Bloquear imputación de tiempos')
    
    
class ProjectTaskEntrega(models.Model):
    _name = 'project.task.entrega'
    _description = "Entregas (Tareas)"

    name = fields.Char("Observaciones")
    fecha = fields.Date("Fecha")
    entregado = fields.Float("Entregado")
    task_id = fields.Many2one("project.task")
    
    
    
