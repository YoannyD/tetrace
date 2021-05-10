# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class Estado(models.Model):
    _name = 'tetrace.project_state'
    _description = "Estados"
    _order = "sequence,name"

    sequence = fields.Integer('Secuencia')
    name = fields.Char('Nombre', required=True, translate=True)
    project_ids = fields.One2many('project.project', 'estado_id')


class MotivoCancelacion(models.Model):
    _name = 'tetrace.motivo_cancelacion'
    _description = "Motivos cancelación"
    _order = "sequence,name"

    sequence = fields.Integer("Secuencia")
    name = fields.Char('Motivo', translate=True)
    project_ids = fields.One2many("project.project", "motivo_cancelacion_id")


class Project(models.Model):
    _inherit = 'project.project'

    def _default_estado_id(self):
        return self.env['tetrace.project_state'].search([], limit=1).id

    descripcion = fields.Text("Descripción", translate=True)
    estado_id = fields.Many2one('tetrace.project_state', string='Estado', ondelete='restrict', tracking=True,
                                index=True, group_expand='_read_group_estado_ids',
                                copy=False, default=lambda self: self._default_estado_id())
    product_tmpl_diseno_ids = fields.One2many("product.template", "project_template_diseno_id")
    color = fields.Integer(related="sale_order_id.tipo_servicio_id.color")
    sale_order_state = fields.Selection(related="sale_order_id.state")
    partner_latitude = fields.Float('Geo Latitude', digits=(16, 5))
    partner_longitude = fields.Float('Geo Longitude', digits=(16, 5))
    partner_geo_id = fields.Many2one("res.partner", string="Geolocalización")
    url_proyecto = fields.Char("URL proyecto", translate=True)
    maps = fields.Char("Maps")
    fecha_inicio = fields.Date("Fecha inicio")
    fecha_cancelacion = fields.Date("Fecha cancelación")
    fecha_finalizacion = fields.Date("Fecha finalización")
    motivo_cancelacion_id = fields.Many2one('tetrace.motivo_cancelacion', string="Motivo cancelación")
    empresa_destino_nombre = fields.Char("Nombre empresa destino")
    cif_destino_nombre = fields.Char("CIF empresa destino")
    direccion = fields.Char("Dirección")
    nombre_parque = fields.Char("Nombre parque")
    partner_ids = fields.Many2many("res.partner", string="Contactos")
    tecnico_calendario_ids = fields.One2many('tetrace.tecnico_calendario', 'project_id')
    visible_btn_crear_tareas_faltantes = fields.Boolean("Visible botón crear tareas faltantes", store=True,
                                                        compute="_compute_visible_btn_crear_tareas_faltantes")

    @api.constrains("fecha_cancelacion", "motivo_cancelacion_id")
    def _check_motivo_cancelacion_id(self):
        for r in self:
            if r.fecha_cancelacion and not r.motivo_cancelacion_id:
                raise ValidationError(_("Si hay fecha de cancelación es olbigatorio indicar el motivo"))

    def _table_get_empty_so_lines(self):
        """ get the Sale Order Lines having no timesheet but having generated a task or a project """
        so_lines = self.sudo() \
            .mapped('sale_line_id.order_id.order_line') \
            .filtered(lambda
                          sol: sol.is_service and sol.product_id.service_policy == 'delivered_timesheet' and not sol.is_expense and not sol.is_downpayment)
        # include the service SO line of SO sharing the same project
        sale_order = self.env['sale.order'].search([('project_id', 'in', self.ids)])
        return set(so_lines.ids) | set(sale_order.mapped('order_line').filtered(lambda
                                                                                    sol: sol.is_service and sol.product_id.service_policy == 'delivered_timesheet' and not sol.is_expense).ids), set(
            so_lines.mapped('order_id').ids) | set(sale_order.ids)

    @api.depends("sale_order_id", "sale_order_state")
    def _compute_visible_btn_crear_tareas_faltantes(self):
        for r in self:
            if r.sale_order_id and r.sale_order_state == 'sale':
                r.visible_btn_crear_tareas_faltantes = True
            else:
                r.visible_btn_crear_tareas_faltantes = False

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
        action['views'] = [(False, 'tree'), (False, 'kanban'), (False, 'form'), (False, 'calendar'), (False, 'pivot'),
                           (False, 'graph'), (False, 'activity'), (False, 'gantt'), (False, 'map')]
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
        res.actualizar_deadline_tareas_activacion()
        res.actualizar_deadline_tareas_desactivacion()
        res.default_etapa_tareas()
        return res

    def write(self, vals):
        if 'fecha_inicio' in vals:
            projects_activacion = self.filtered(lambda x: not x.fecha_inicio)
            projects_modificacion = self.filtered(lambda x: x.fecha_inicio)
        
        res = super(Project, self).write(vals)
        vals = self.actualizar_vals(vals)
        if 'name' in vals or 'partner_latitude' in vals or 'partner_longitude' in vals:
            self.actualizar_geo_partner()

        if 'fecha_inicio' in vals:
            self.actualizar_deadline_tareas_activacion()
            projects_activacion.enviar_email_estado_proyecto('activacion')
            projects_modificacion.enviar_email_estado_proyecto('modificacion')

        if 'fecha_cancelacion' in vals or 'fecha_finalizacion' in vals:
            self.actualizar_deadline_tareas_desactivacion()
            
        if 'fecha_finalizacion' in vals:
            self.enviar_email_estado_proyecto('desactivacion')
            
        if 'partner_id' in vals:
            self.actualizar_partner_task()
        return res

    def actualizar_deadline_tareas_activacion(self):
        for r in self:
            if not r.fecha_inicio:
                continue

            for task in r.tasks.filtered(lambda x: x.tipo != 'activacion' or not x.stage_id.no_update_deadline):
                date_deadline = fields.Date.from_string(r.fecha_inicio) + timedelta(days=task.deadline_inicio)
                task.write({'date_deadline': date_deadline})

    def actualizar_deadline_tareas_desactivacion(self):
        for r in self:
            fecha = None
            if r.fecha_finalizacion:
                fecha = r.fecha_finalizacion
            elif r.fecha_cancelacion:
                fecha = r.fecha_cancelacion

            if not fecha:
                continue

            for task in r.tasks.filtered(lambda x: x.tipo != 'activacion' or not x.stage_id.no_update_deadline):
                date_deadline = fields.Date.from_string(fecha) + timedelta(days=task.deadline_inicio)
                task.write({'date_deadline': date_deadline})

    def actualizar_partner_task(self):
        for r in self:
            if r.partner_id:
                r.tasks.write({'partner_id': r.partner_id.id})
                
    @api.model
    def actualizar_vals(self, vals):
        if "estado_id" in vals and vals.get("estado_id") != 4:
            vals.update({"motivo_cancelacion_id": False})
        return vals

    def actualizar_geo_partner(self):
        for r in self:
            values = {
                'name': _("Geolocalización %s") % r.name,
                'partner_latitude': r.partner_latitude,
                'partner_longitude': r.partner_longitude,
            }

            if not r.partner_geo_id:
                values.update({'project_geo_ids': [(6, 0, [r.id])]})
                self.env['res.partner'].with_context(no_actualizar=True).create(values)
            else:
                r.partner_geo_id.with_context(no_actualizar=True).write(values)

    def default_etapa_tareas(self):
        for r in self:
            r.type_ids = [(4, 4), (4, 5), (4, 10), (4, 269)]

    def view_procesos_seleccion_tree(self):
        self.ensure_one()
        applicant_ids = []
        for task in self.tasks:
            applicant_ids += task.applicant_ids.ids
        action = self.env['ir.actions.act_window'].for_xml_id('hr_recruitment', 'crm_case_categ0_act_job')
        action.update({'domain': [('id', 'in', applicant_ids)]})
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

    def action_gastos(self):
        self.ensure_one()
        return {
            'name': _('Gastos'),
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'domain': [
                ('analytic_account_id', '=', self.analytic_account_id.id),
                ('move_id.type', 'in', ['in_invoice', 'in_refund', 'in_receipt'])
            ]
        }

    def action_ingresos(self):
        self.ensure_one()
        return {
            'name': _('Ingresos'),
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'domain': [
                ('analytic_account_id', '=', self.analytic_account_id.id),
                ('move_id.type', 'in', ['out_invoice', 'out_refund', 'out_receipt'])
            ]
        }

    def action_crear_tareas_act_desc(self):
        self.ensure_one()
        wizard = self.env['tetrace.crear_tareas_act_desc'].create({'project_id': self.id})
        return wizard.open_wizard()

    def action_crear_tareas_faltantes(self):
        self.ensure_one()
        if not self.sale_order_id:
            return

        if self.sale_order_id.state != 'sale':
            raise UserError(_("El pedido de venta tiene que estar confirmado"))

        self.sale_order_id.action_generar_proyecto()
        self.sale_order_id.mapped('order_line').sudo().with_context(
            force_company=self.sale_order_id.company_id.id,
        )._timesheet_service_generation()
        
    def enviar_email_tareas_asignadas(self):
        email_template = self.env.ref('tetrace.email_template_project_task_assigned', raise_if_not_found=False)
        for r in self:
            user_asignados_ids = r.get_all_user_assigned_task()
            if not user_asignados_ids:
                continue
                
            users = self.env['res.users'].search([
                ('id', 'in', user_asignados_ids),
                ('partner_id', '!=', False)
            ])
            for user in users:
                user_tasks = r.tasks.filtered(lambda x: x.user_id.id == user.id and not x.notify_by_email)
                if not user_tasks:
                    continue
                    
                email_template.sudo()\
                .with_context(tasks=user_tasks, lang=user.lang or r.partner_id.lang)\
                .send_mail(r.id, force_send=True, email_values={'recipient_ids': [(4, user.partner_id.id)]})
                user_tasks.write({'notify_by_email': True})
                
    def enviar_email_estado_proyecto(self, estado):
        email_template = self.env.ref('tetrace.email_template_project_estado', raise_if_not_found=False)
        for r in self:
            user_asignados_ids = r.get_all_user_assigned_task()
            if not user_asignados_ids:
                continue
                
            users = self.env['res.users'].search([
                ('id', 'in', user_asignados_ids),
                ('partner_id', '!=', False)
            ])
            for user in users:
                if estado == 'activacion':
                    subject = _("El proyecto %s ha sido activado" % r.name)
                elif estado == 'desactivacion':
                    subject = _("El proyecto %s ha sido desactivado" % r.name)
                elif estado == 'modificacion':
                    subject = _("El proyecto %s ha sido modificado" % r.name)
                
                email_template.sudo()\
                .with_context(estado=estado, lang=user.lang or r.partner_id.lang)\
                .send_mail(r.id, force_send=True, email_values={
                    'subject': subject,
                    'recipient_ids': [(4, user.partner_id.id)]
                })
        
    def get_all_user_assigned_task(self):
        self.ensure_one()
        user_ids = []
        for task in self.tasks:
            if task.user_id and task.user_id.id not in user_ids:
                user_ids.append(task.user_id.id)
        return user_ids
    

class TecnicoCalendario(models.Model):
    _name = 'tetrace.tecnico_calendario'
    _description = "Técnicos calendarios"

    project_id = fields.Many2one('project.project', string="Proyecto", required=True)
    employee_id = fields.Many2one('hr.employee', string="Técnico", required=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string="Calendario", required=True)
