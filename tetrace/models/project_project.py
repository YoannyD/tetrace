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
        return self.env['tetrace.project_state'].search([('id', '=', 3)], limit=1).id

    descripcion = fields.Text("Descripción", translate=True)
    estado_id = fields.Many2one('tetrace.project_state', string='Estado', ondelete='restrict', tracking=True,
                                index=True, group_expand='_read_group_estado_ids',
                                copy=False, default=lambda self: self._default_estado_id())
    product_tmpl_diseno_ids = fields.One2many("product.template", "project_template_diseno_id")
    color = fields.Integer(related="sale_order_id.tipo_servicio_id.color")
    sale_order_state = fields.Selection(related="sale_order_id.state")
    sale_order_ref_proyecto = fields.Char(related="sale_order_id.ref_proyecto")
    partner_latitude = fields.Float('Geo Latitude', digits=(16, 5))
    partner_longitude = fields.Float('Geo Longitude', digits=(16, 5))
    partner_geo_id = fields.Many2one("res.partner", string="Geolocalización")
    url_proyecto = fields.Char("URL proyecto", translate=True)
    maps = fields.Char("Maps")
    fecha_inicio = fields.Date("Fecha inicio", track_visibility='onchange')
    fecha_cancelacion = fields.Date("Fecha cancelación", track_visibility='onchange')
    fecha_finalizacion = fields.Date("Fecha finalización", track_visibility='onchange')
    motivo_cancelacion_id = fields.Many2one('tetrace.motivo_cancelacion', string="Motivo cancelación")
    empresa_destino_nombre = fields.Char("Nombre empresa destino")
    cif_destino_nombre = fields.Char("CIF empresa destino")
    direccion = fields.Char("Dirección")
    nombre_parque = fields.Char("Nombre parque")
    partner_ids = fields.Many2many("res.partner", string="Contactos")
    tecnico_calendario_ids = fields.One2many('tetrace.tecnico_calendario', 'project_id')
    tecnico_ids = fields.Many2many("hr.employee", compute="_compute_tecnico_ids", store=True, string="Técnicos", track_visibility='onchange')
    visible_btn_crear_tareas_faltantes = fields.Boolean("Visible botón crear tareas faltantes", store=True,
                                                        compute="_compute_visible_btn_crear_tareas_faltantes")
    experiencia_ids = fields.One2many('tetrace.experiencia', 'project_id', track_visibility='onchange')
    tipo_proyecto_name = fields.Char(related="sale_order_id.tipo_proyecto_name", store=True)
    clasificacion = fields.Selection(selection=[
        ('service', 'servicio'),
        ('it', 'IT'),
        ('planner', 'Planner'),
        ('estructural', 'Estructural'),
    ], string='Clasificación Tetrace', copy=True)
    proyecto_necesidad_ids = fields.One2many('tetrace.proyecto_necesidad', 'project_id', track_visibility='onchange')
    applicant_ids = fields.Many2many('hr.applicant')
    company_coordinador_id = fields.Many2one('res.company', string="Compañia coordinadora")
    document_project_count = fields.Integer('Documentos', compute="_compute_document_project")
    analitica_cerrada = fields.Boolean(related="analytic_account_id.analitica_cerrada")
    analytic_account_code = fields.Char(related="analytic_account_id.code")
    mostrar_btn_cerrar_analitica = fields.Boolean("Mostrar botón cerrar cuenta analítica", 
                                                  compute="_compute_mostrar_btn_cerrar_analitica")
    prioridad = fields.Selection(selection=[
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], string='Prioridad')
    departamento = fields.Char(string="Departamento" , related="propietario.employee_ids.department_id.display_name")
    propietario= fields.Many2one('res.users', string="Propietario")
    key_user= fields.Many2many('res.users')
    recurso_it = fields.Selection(selection=[
        ('interno', 'Interno'),
        ('yoanny', 'Yoanny'),
        ('voodoo', 'Voodoo'),
        ('Landoo', 'Landoo'),
    ], string='Recurso IT')
    estimacion_horas= fields.Integer(string="Estimación horas")
    quickwin= fields.Boolean('QuickWin')
    estimacion_coste= fields.Monetary(string="Estimación coste")

    
    @api.constrains("fecha_cancelacion", "motivo_cancelacion_id")
    def _check_motivo_cancelacion_id(self):
        for r in self:
            if r.fecha_cancelacion and not r.motivo_cancelacion_id:
                raise ValidationError(_("Si hay fecha de cancelación es olbigatorio indicar el motivo"))
            
    def _compute_mostrar_btn_cerrar_analitica(self):
        for r in self:
            r.mostrar_btn_cerrar_analitica = True if self.analytic_account_code == self.sale_order_ref_proyecto else False
            
    @api.depends("tecnico_calendario_ids.employee_id")
    def _compute_tecnico_ids(self):
        for r in self:
            r.tecnico_ids = [(6, 0, [tc.employee_id.id for tc in r.tecnico_calendario_ids])]
            
    def _compute_document_project(self):
        for r in self:
            docs_project = self.env['documents.document'].search_count([
                ('res_model', '=', 'project.project'),
                ('res_id', '=', r.id),
            ])
            
            r.document_project_count = docs_project
            
    def _table_get_empty_so_lines(self):
        """ get the Sale Order Lines having no timesheet but having generated a task or a project """
        so_lines = self.sudo() \
            .mapped('sale_line_id.order_id.order_line') \
            .filtered(lambda sol: sol.is_service and sol.product_id.service_policy == 'delivered_timesheet' and not sol.is_expense and not sol.is_downpayment)
        # include the service SO line of SO sharing the same project
        sale_order = self.env['sale.order'].search([('project_id', 'in', self.ids)])
        return set(so_lines.ids) | set(sale_order.mapped('order_line').filtered(lambda sol: sol.is_service and sol.product_id.service_policy == 'delivered_timesheet' and not sol.is_expense).ids), set(so_lines.mapped('order_id').ids) | set(sale_order.ids)

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
        res.default_etapa_tareas()
        if res.proyecto_necesidad_ids:
            res.tasks.filtered(lambda x: x.busqueda_perfiles).write({'activada': True})
        return res

    def write(self, vals):
        if 'fecha_inicio' in vals:
            projects_activacion = self.filtered(lambda x: not x.fecha_inicio)
            projects_modificacion = self.filtered(lambda x: x.fecha_inicio)
        
        res = super(Project, self).write(vals)
        vals = self.actualizar_vals(vals)
        
        if 'company_coordinador_id' in vals:
            for r in self:
                r.tasks.write({'company_coordinador_id': r.company_coordinador_id.id})

        if 'experiencia_ids' in vals or 'tecnico_calendario_ids' in vals:
            self.actualizar_experiencias_tecnicos()
            
        if 'fecha_inicio' in vals:
            projects_activacion.enviar_email_estado_proyecto('activacion')
            projects_modificacion.enviar_email_estado_proyecto('modificacion')
            for task in projects_activacion.tasks.filtered(lambda x: not x.tarea_individual):
                date_deadline = fields.Date.from_string(task.project_id.fecha_inicio) + timedelta(days=task.deadline)
                task.write({'date_deadline': date_deadline})
            
        if vals.get('fecha_finalizacion'):
            for r in self:
                for task in r.tasks.filtered(lambda x: not x.tarea_individual):
                    date_deadline = fields.Date.from_string(task.project_id.fecha_finalizacion) + timedelta(days=task.deadline)
                    task.write({'date_deadline': date_deadline})
            
        if vals.get('fecha_cancelacion') or vals.get('fecha_finalizacion'):
            self.enviar_email_estado_proyecto('desactivacion')
              
        if 'partner_id' in vals:
            self.actualizar_partner_task()
            
        if 'proyecto_necesidad_ids' in vals:
            for r in self:
                r.tasks.filtered(lambda x: x.busqueda_perfiles).write({'activada': True})
            
        return res

    def actualizar_experiencias_tecnicos(self):
        ResumeLine = self.env['hr.resume.line']
        ExperienciaTecnicoProyecto = self.env['tetrace.experiencia_tecnico_proyecto']
        for r in self:
            for tecnico in r.tecnico_calendario_ids: 
                for experiencia in r.experiencia_ids:
                    experiencia_tecnico_proyecto = ExperienciaTecnicoProyecto.search([
                        ('experiencia_id', '=', experiencia.id),
                        ('employee_id', '=', tecnico.employee_id.id),
                        ('project_id', '=', r.id),
                        ('resume_line_id', '!=', False),
                    ], limit=1)
                    
                    if experiencia_tecnico_proyecto:
                        if not tecnico.job_id or not tecnico.fecha_inicio:
                            experiencia_tecnico_proyecto.resume_line_id.unlink()
                            continue
                        
                        if tecnico.job_id.id != experiencia.job_id.id:
                            experiencia_tecnico_proyecto.resume_line_id.unlink()
                            experiencia_tecnico_proyecto = None
                            experiencia = self.env['tetrace.experiencia'].search([
                                ('job_id', '=', tecnico.job_id.id),
                                ('project_id', '=', r.id)
                            ], limit=1)
                            if not experiencia:
                                continue
                    
                    values = {
                        'employee_id': tecnico.employee_id.id,
                        'name': experiencia.name,
                        'description': experiencia.descripcion,
                        'date_start': tecnico.fecha_inicio,
                        'date_end': tecnico.fecha_fin
                    }
                    
                    if experiencia_tecnico_proyecto:
                        experiencia_tecnico_proyecto.resume_line_id.write(values)
                    else:
                        resume_line = ResumeLine.create(values)
                        self.env['tetrace.experiencia_tecnico_proyecto'].create({
                            'experiencia_id': experiencia.id,
                            'employee_id': tecnico.employee_id.id,
                            'project_id': r.id,
                            'resume_line_id': resume_line.id
                        })
                        
        for r in self:
            domain = [
                ('project_id', '=', r.id),
                ('resume_line_id', '!=', False)
            ]
            
            employee_ids = [e.employee_id.id for e in r.tecnico_calendario_ids.filtered(lambda x: x.job_id and x.employee_id and x.fecha_inicio)]
            if r.experiencia_ids and employee_ids:
                domain = ['|',
                    ('experiencia_id', 'not in', r.experiencia_ids.ids),
                    ('employee_id', 'not in', employee_ids)
                ]
            elif r.experiencia_ids:
                domain = [('experiencia_id', 'not in', r.experiencia_ids.ids)]
            elif employee_ids:
                domain = [('employee_id', 'not in', employee_ids)]
            
            experiencia_tecnico_proyecto = ExperienciaTecnicoProyecto.search(domain)
            for etp in experiencia_tecnico_proyecto:
                etp.resume_line_id.unlink()
            
    def actualizar_deadline_tareas_activacion(self):
        for r in self:
            if not r.fecha_inicio:
                continue

            for task in r.tasks.filtered(lambda x: x.tipo == 'activacion' and x.tarea_individual):
                date_deadline = fields.Date.from_string(r.fecha_inicio) + timedelta(days=task.deadline)
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

    def default_etapa_tareas(self):
        for r in self:
            r.type_ids = [(4, 4), (4, 5), (4, 10), (4, 269)]

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
        if self.fecha_finalizacion and self.fecha_finalizacion < fields.Date.today():
            raise UserError(_("El proyecto ya está finalizado"))
        
        wizard = self.env['tetrace.activar_tarea'].create({"project_id": self.id})
        
        tecnico_proyecto_activo = self.env['tetrace.tecnico_calendario'].search([
            ('project_id', '=', self.id),
            ('fecha_fin', '=', None),
        ])  
        
        for tecnico in tecnico_proyecto_activo:
            self.env['tetrace.activar_tarea_detalle'].create({
                'activar_tarea_id': wizard.id,
                'employee_id': tecnico.employee_id.id,
                'fecha_fin': tecnico.fecha_fin
            })
            
        return wizard.open_wizard()

    def view_analitica_tree(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('analytic', 'account_analytic_line_action')
        action["domain"] = [('account_id', '=', self.analytic_account_id.id)]
        action["context"] = {'search_default_group_date': 1, 'default_account_id': self.analytic_account_id.id}
        return action

    def action_gastos(self):
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
    
    def action_resultado(self):
        return {
            'name': _('Resultado'),
            'view_mode': 'dashboard,pivot,graph,tree',
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'domain': ["&",
                ('analytic_account_id', '=', self.analytic_account_id.id),
                "|",("account_id.user_type_id",'=',"Ingreso"),("account_id.user_type_id",'=',"Gastos")
            ]
        }
    
    def action_view_entregas(self):
        return {
            'name': _('Entregas'),
            'view_mode': 'tree,form',
            'res_model': 'project.task.entrega',
            'type': 'ir.actions.act_window',
            'domain': [('task_id.project_id', '=', self.id)],
            'context': {'project_id': self.id, 'employee_ids': self.tecnico_ids.ids}
        }

    def action_crear_tareas_act_desc(self):
        if self.fecha_finalizacion and self.fecha_finalizacion < fields.Date.today():
            raise UserError(_("El proyecto ya está finalizado"))
        
        today = fields.Date.today()
        tecnicos_proyecto = self.env['tetrace.tecnico_calendario'].search([('project_id', '=', self.id)]) 
        
        employees = self.env['hr.employee'].search([('id', 'not in', [tp.employee_id.id for tp in tecnicos_proyecto])])
        
        tecnico_proyecto_inactivos = self.env['tetrace.tecnico_calendario'].search([
            ('project_id', '=', self.id),
            '|',
            ('fecha_fin', '=', None),
            ('fecha_fin', '<=', today),
        ])
        proyecto_employee_inactivos_ids = [ti.employee_id.id for ti in tecnico_proyecto_inactivos]
        
        
        tecnico_proyecto_activo = self.env['tetrace.tecnico_calendario'].search([
            ('project_id', '=', self.id),
            '|',
            ('fecha_fin', '=', None),
            ('fecha_fin', '>=', today)
        ])
        proyecto_employee_activos_ids = [ta.employee_id.id for ta in tecnico_proyecto_activo]   
            
        wizard = self.env['tetrace.crear_tareas_act_desc'].create({
            'project_id': self.id,
            'tecnico_inactivos_ids': [(6, 0, employees.ids + proyecto_employee_inactivos_ids)],
            'tecnico_activo_ids': [(6, 0, proyecto_employee_activos_ids)]
        })
        return wizard.open_wizard()
    
    def action_crear_tareas_faltantes(self):
        if self.sale_order_id.state != 'sale':
            raise UserError(_("El pedido de venta tiene que estar confirmado"))
        
        project_theme = None
        try:
            project_theme_id = int(self.env['ir.config_parameter'].sudo().get_param('template_act_project_id'))
            project_theme = self.env['project.project'].sudo().search([('id', '=', project_theme_id)], limit=1)
        except:
            pass
        
        if not project_theme:
           raise UserError(_("Tiene que configurar una plantilla de proyecto.")) 
        
        self.sale_line_id.copy_tasks(project_theme.sudo().tasks, self)
        
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
                user_tasks = r.tasks.filtered(lambda x: x.user_id.id == user.id and x.desde_plantilla and not x.notify_by_email)
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
                    user_tasks = r.tasks.filtered(lambda x: x.user_id.id == user.id and x.tipo == 'activacion')
                elif estado == 'desactivacion':
                    subject = _("El proyecto %s ha sido desactivado" % r.name)
                    user_tasks = r.tasks.filtered(lambda x: x.user_id.id == user.id and x.tipo == 'desactivacion')
                elif estado == 'modificacion':
                    subject = _("El proyecto %s ha sido modificado" % r.name)
                    user_tasks = r.tasks.filtered(lambda x: x.user_id.id == user.id and x.tipo == 'activacion')
                
                if not user_tasks:
                    continue
                
                email_template.sudo()\
                    .with_context(estado=estado, tasks=user_tasks, lang=user.lang or r.partner_id.lang)\
                    .send_mail(r.id, force_send=True, email_values={
                        'subject': subject,
                        'recipient_ids': [(4, user.partner_id.id)]
                    })
        
    def get_all_user_assigned_task(self):
        user_ids = []
        for task in self.tasks:
            if task.user_id and task.user_id.id not in user_ids:
                user_ids.append(task.user_id.id)
        return user_ids
    
    def view_documentos(self):
        action = self.env['ir.actions.act_window'].for_xml_id('documents', 'document_action')
        documents = self.env['documents.document'].search([
            ('res_model', '=', 'project.project'),
            ('res_id', '=', self.id),
        ])
    
        action.update({
            'context': {'res_model': 'project.project', 'res_id': self.id},
            'domain': [('id', 'in', documents.ids)]
        })
        return action
    
    def update_followers(self):
        for project in self:
            if project.user_id.partner_id.id not in project.message_follower_ids.mapped('partner_id').ids:
                project.message_follower_ids = [(0, 0, {
                    'partner_id': project.user_id.partner_id.id,
                    'res_model': 'project.project',
                    'res_id': project.id,
                })]
            tasks = self.env['project.task'].sudo().search([('project_id', '=', project.id)])
            for task in tasks:
                if project.user_id.partner_id.id not in task.message_follower_ids.mapped('partner_id').ids:
                    task.message_follower_ids = [(0, 0, {
                        'partner_id': project.user_id.partner_id.id,
                        'res_model': 'project.task',
                        'res_id': task.id,
                    })]
    
    def cerrar_cuenta_analitica(self):
        if not self.analytic_account_id:
            return
        
        if self.analytic_account_code != self.sale_order_ref_proyecto:
            raise UserError(_("No puedes cerrar una cuenta analítica que no sea del proyecto."))
            
        self.analytic_account_id.write({'analitica_cerrada': True})
        
    def action_vacia_fecha_finalizacion(self):
        self.write({'fecha_finalizacion': None})
        
    def action_vacia_fecha_cancelacion(self):
        self.write({'fecha_cancelacion': None})