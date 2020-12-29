# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import re
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    name = fields.Char(compute="_compute_name", store=True)
    ref_proyecto = fields.Char('Referencia proyecto', copy=False)
    ejercicio_proyecto = fields.Integer('Ejercicio', default=fields.Date.today().strftime("%y"), copy=False)
    tipo_proyecto_id = fields.Many2one('tetrace.tipo_proyecto', string="Tipo de proyecto", copy=False)
    num_proyecto = fields.Char('Nº proyecto', copy=False)
    partner_siglas = fields.Char(related="partner_id.siglas")
    tipo_servicio_id = fields.Many2one('tetrace.tipo_servicio', string="Tipo de servicio", copy=False)
    proyecto_country_id = fields.Many2one('res.country', string="País", copy=False)
    nombre_proyecto = fields.Char('Nombre proyecto', copy=False)
    detalle_proyecto = fields.Char('Detalle proyecto', copy=False)
    descripcion_proyecto = fields.Char('Descripción proyecto', copy=False)
    cabecera_proyecto = fields.Html('Cabecera proyecto', copy=False)
    version_ids = fields.One2many('tetrace.sale_order_version', 'sale_order_id')
    version_count = fields.Integer('Versiones', compute="_compute_version")
    referencia_proyecto_antigua = fields.Char("Ref. proyecto antigua", copy=False)
    coordinador_proyecto_id = fields.Many2one("res.users", string="Coordinador proyecto")
    seguidor_proyecto_ids = fields.Many2many("res.users", string="Seguidores proyecto")
    visible_btn_generar_proyecto = fields.Boolean("Visible botón generar proyecto", store=True,
                                                  compute="_compute_visible_btn_generar_proyecto")
    prevision_facturacion_ids = fields.One2many("tetrace.prevision_facturacion", "order_id")
    total_previsto = fields.Monetary("Total previsto", compute="_compute_prevision_facturacion", store=True)
    total_facturado = fields.Monetary("Total facturado", compute="_compute_prevision_facturacion", store=True)
    project_estado_id = fields.Many2one("tetrace.project_state", compute="_compute_project_estado_id", 
                                        string="Estado proyecto", store=True)
    rfq = fields.Char("RFQ")

    sql_constraints = [
        ('ref_proyecto_uniq', 'check(1=1)', "No error")
    ]

    @api.constrains("num_proyecto")
    def _check_num_proyecto(self):
        for r in self:
            if r.num_proyecto:
                if len(r.num_proyecto) != 4:
                    raise ValidationError("El Nº de proyecto tiene que ser de 4 caracteres.")
                    
    @api.constrains("referencia_proyecto_antigua")
    def _check_referencia_proyecto_antigua(self):
        for r in self:
            if  r.referencia_proyecto_antigua and re.fullmatch(r'\d{4}\.\d{4}',r.referencia_proyecto_antigua) == None:
                raise ValidationError("La referencia de proyecto antigua tiene que seguir el patrón 9999.9999.")
                    
    @api.depends("rfq", "ref_proyecto")
    def _compute_name(self):
        for r in self:
            if r.ref_proyecto:
                r.name = r.ref_proyecto
            elif r.rfq:
                r.name = r.rfq
                    
    @api.depends("project_ids.estado_id")
    def _compute_project_estado_id(self):
        for r in self:
            if r.project_ids:
                r.project_estado_id = r.project_ids[0].estado_id.id
            else:
                r.project_estado_id = None
                    
    def _compute_version(self):
        for r in self:
            r.version_count = len(r.version_ids)

    @api.depends("prevision_facturacion_ids.facturado")
    def _compute_prevision_facturacion(self):
        for r in self:
            previsto = 0
            facturado = 0
            for prevision in r.prevision_facturacion_ids:
                if prevision.facturado:
                    facturado += prevision.importe
                else:
                    previsto += prevision.importe
                    
            r.update({
                'total_facturado': facturado,
                'total_previsto': previsto
            })
            
    @api.depends('order_line.product_id.project_id')
    def _compute_tasks_ids(self):
        for order in self:
            task_ids = []
            for project in order.project_ids:
                task_ids += project.task_ids.ids
            tasks = self.env['project.task'].search([
                ('id', 'in', task_ids),
                ('activada', '=', True)
            ])
            order.update({
                'tasks_ids': [(6, 0, tasks.ids)],
                'tasks_count': len(tasks)
            })
            
    @api.depends("order_line.product_id", "order_line.product_id.project_template_diseno_id", 
                'order_line.product_id', 'order_line.project_id')
    def _compute_visible_btn_generar_proyecto(self):
        for r in self:
            visible = False
            if not r.project_ids:
                for line in r.order_line:
                    if line.product_id and line.product_id.project_template_diseno_id:
                        visible = True
                        break
            r.update({'visible_btn_generar_proyecto': visible})
             
    @api.onchange('ejercicio_proyecto', 'tipo_proyecto_id', 'num_proyecto','referencia_proyecto_antigua')
    def _onchange_ref_proyecto(self):
        for r in self:
            r.ref_proyecto = r.generar_ref_proyecto()

    @api.onchange('partner_siglas', 'tipo_servicio_id', 'proyecto_country_id', 'detalle_proyecto')
    def _onchange_nombre_proyecto(self):
        for r in self:
            r.nombre_proyecto = r.generar_nombre_proyecto()

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if 'tipo_proyecto_id' in vals or 'num_proyecto' in vals:
            ref_proyecto = res.generar_ref_proyecto()
            res.with_context(cambiar_ref_proyecto=True).write({'ref_proyecto': ref_proyecto})

        if 'tipo_servicio_id' in vals or 'proyecto_country_id' in vals or 'detalle_proyecto' in vals:
            res.with_context(cambiar_nombre_proyecto=True).write({'nombre_proyecto': res.generar_nombre_proyecto()})

        return res

    def write(self, vals):
        if 'ref_proyecto' in vals and not self.env.context.get('cambiar_ref_proyecto'):
            vals.pop('ref_proyecto')

        if 'nombre_proyecto' in vals and not self.env.context.get('cambiar_nombre_proyecto'):
            vals.pop('nombre_proyecto')

        if 'referencia_proyecto_antigua' in vals and vals.get('referencia_proyecto_antigua'):
            vals.update({'ref_proyecto' : vals.get('referencia_proyecto_antigua')})
            
        res = super(SaleOrder, self).write(vals)

        if 'tipo_proyecto_id' in vals or 'nombre_proyecto' in vals or 'num_proyecto' in vals:
            for r in self:
                ref_proyecto = r.generar_ref_proyecto()
                r.with_context(cambiar_ref_proyecto=True).write({'ref_proyecto': ref_proyecto})
                    
        if 'tipo_proyecto_id' in vals or 'nombre_proyecto' in vals or 'num_proyecto' in vals or \
            'state' in vals:
            for r in self:
                if r.state == 'sale' and not r.ref_proyecto:
                    raise ValidationError("¡La referencia de proyecto tiene que ser única!")

        if 'tipo_servicio_id' in vals or 'proyecto_country_id' in vals or 'detalle_proyecto' in vals:
            for r in self:
                nombre_proyecto = r.generar_nombre_proyecto()
                r.with_context(cambiar_nombre_proyecto=True).write({'nombre_proyecto': nombre_proyecto})

        if 'tipo_proyecto_id' in vals or 'nombre_proyecto' in vals or 'num_proyecto' in vals or \
            'tipo_servicio_id' in vals or 'proyecto_country_id' in vals or 'detalle_proyecto' in vals \
            or 'referencia_proyecto_antigua' in vals or 'partner_id' in vals:
            self.actualizar_datos_proyecto()

        if vals.get('coordinador_proyecto_id'):
            for r in self:
                r.project_ids.write({'user_id': r.coordinador_proyecto_id.id})
                
        if vals.get('partner_id'):
            for r in self:
                r.project_ids.write({'partner_id': r.partner_id.id})
         
        return res
    
    def generar_ref_proyecto(self):
        self.ensure_one()
        if self.ejercicio_proyecto and self.tipo_proyecto_id and self.num_proyecto:
            return "P%s%s.%s" % (self.ejercicio_proyecto, self.tipo_proyecto_id.tipo if self.tipo_proyecto_id else '', self.num_proyecto)            
        elif self.referencia_proyecto_antigua:
            return self.referencia_proyecto_antigua     
        else:
            return None

    def generar_nombre_proyecto(self):
        self.ensure_one()
        return "%s %s %s %s" % (
                self.partner_siglas or '',
                self.tipo_servicio_id.name if self.tipo_servicio_id else '',
                self.proyecto_country_id.code if self.proyecto_country_id else '',
                self.detalle_proyecto or ''
            )

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        self.actualizar_datos_proyecto()
        self.send_mail_seguidores()
        self.project_ids.write({'estado_id': self.env.ref("tetrace.project_state_en_proceso").id})
        return res

    def actualizar_datos_proyecto(self):
        for r in self:
            if r.project_ids:
                if not r.ref_proyecto or not r.nombre_proyecto:
                    raise ValidationError('La referencia y el nombre de proyecto son obligatorios.')
                    
                name = "%s %s" % (r.ref_proyecto, r.nombre_proyecto)
                r.project_ids.write({'name': name})
                for p in r.project_ids:
                    p.analytic_account_id.write({
                        'name': name,
                        'partner_id': r.partner_id.id,
                        'company_id': None
                    })

    def action_crear_version(self):
        self.ensure_one()
        wizard = self.env['tetrace.crear_version'].create({
            'sale_order_id': self.id,
            'version': self.env['tetrace.sale_order_version'].siguiente_version(self.id)
        })
        return wizard.open_wizard()
    
    def action_generar_proyecto(self):
        self.ensure_one()
        if self.project_ids:
            return
        
        if not self.ref_proyecto or not self.nombre_proyecto:
            raise ValidationError("Para crear el proyecto es obligatorio indicar el nombre y la referencia.")
        
        # Crear el proyecto con la plantilla diseño del primer producto que la tenga
        project = None
        project_template_diseno_ids = []
        for line in self.order_line:
            if line.product_id.service_tracking == 'task_in_project' and line.product_id.project_template_diseno_id:
                project_template_diseno_ids.append(line.product_id.project_template_diseno_id.id)
                project = line._timesheet_create_project_diseno()
                break
        
        if not project:
            return
        
        for line in self.order_line:
            if line.product_id.project_template_diseno_id and \
                line.product_id.project_template_diseno_id.id not in project_template_diseno_ids:
                for task in line.product_id.project_template_diseno_id.tasks:
                    task.copy({
                        'project_id': project.id,
                        'sale_line_id': line.id,
                        'partner_id': line.order_id.partner_id.id,
                        'email_from': line.order_id.partner_id.email,
                    })
            line._timesheet_create_task(project)
        self.actualizar_datos_proyecto()
            
    def action_view_task(self):
        action = super(SaleOrder, self).action_view_task()
        action['context'].pop('search_default_sale_order_id', None)
        action['context'].pop('search_default_my_tasks', None)
        
        projects = []
        for task in self.tasks_ids:
            projects.append(task.project_id.id)
            
        action['context'].update({'search_default_project_id': projects})
        return action
    
    def action_view_project_ids(self):
        self.ensure_one()
        view_form_id = self.env.ref('project.edit_project').id
        view_kanban_id = self.env.ref('project.view_project_kanban').id
        action = {
            'type': 'ir.actions.act_window',
            'res_id': self.project_ids[0].id,
            'views': [(view_form_id, 'form'),(view_kanban_id, 'kanban')],
            'view_mode': 'form,kanban',
            'name': _('Projects'),
            'res_model': 'project.project',
        }
        return action
    
    def send_mail_seguidores(self):
        for r in self:
            template = self.env['mail.template'].browse(self.env.ref('tetrace.email_template_confirm_sale_order').id)
            if r.coordinador_proyecto_id:
                template.email_to = r.coordinador_proyecto_id.login
                template.send_mail(r.id, force_send=True)
            
            for seguidor in r.seguidor_proyecto_ids:
                if not seguidor.login:
                    continue
                template.email_to = seguidor.login
                template.send_mail(r.id, force_send=True)
     
    def action_generar_prevision_facturacion(self):
        self.ensure_one()
        wizard = self.env['tetrace.generar_prevision_facturacion'].create({'order_id': self.id})
        return wizard.open_wizard()
                      

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    no_imprimir = fields.Boolean("Archivado")
    product_entregado = fields.Boolean(related="product_id.producto_entrega")
    individual = fields.Boolean("Individual")
    
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        self.individual = self.product_id.individual
        return super(SaleOrderLine, self).product_id_change()
    
    def _timesheet_service_generation(self):
        # Compruebo que el pedido tenga o no proyectos
        project_sale = []
        for r in self:
            if r.order_id.project_ids:
                project_sale.append(r.order_id.id)
            
        super(SaleOrderLine, self)._timesheet_service_generation()
        
        project_template_ids = []
        for r in self:
            if r.product_id.service_tracking == 'task_in_project' and \
                r.product_id.project_template_id and r.order_id.id in project_sale and \
                r.product_id.project_template_id.id not in project_template_ids:
                project_template_ids.append(r.product_id.project_template_id.id)
                for task in r.product_id.project_template_id.tasks:
                    task.copy({
                        'name': task.name,
                        'project_id': r.order_id.project_ids[0].id,
                        'sale_line_id': r.id,
                        'partner_id': r.order_id.partner_id.id,
                        'email_from': r.order_id.partner_id.email,
                        'desde_plantilla': True
                    })
                
    def _timesheet_create_project_prepare_values(self):
        values = super(SaleOrderLine, self)._timesheet_create_project_prepare_values()
        values.update({'user_id': self.order_id.coordinador_proyecto_id.id})
        return values
    
    def _timesheet_create_project(self):
        self.ensure_one()
        if not self.order_id.ref_proyecto or not self.order_id.nombre_proyecto:
            raise ValidationError("Para crear el proyecto es obligatorio indicar el nombre y la referencia.")
        
        if self.order_id.project_ids and self.product_id.service_tracking in ['task_global_project', 'task_in_project']:
            return self.order_id.project_ids[0]

        project = super(SaleOrderLine, self)._timesheet_create_project()
        values = {
            "name": "%s %s" % (self.order_id.ref_proyecto, self.order_id.nombre_proyecto)
        }
        project.write(values)
        
        partner_seguidores_ids = []
        for user in self.order_id.seguidor_proyecto_ids:
            if user.partner_id:
                partner_seguidores_ids.append(user.partner_id.id)
                
        if partner_seguidores_ids:   
            project.with_context(add_followers=True)\
                .message_subscribe(partner_ids=partner_seguidores_ids)
        
        return project
    
    def _timesheet_create_project_diseno(self):
        self.ensure_one()
        if not self.order_id.ref_proyecto or not self.order_id.nombre_proyecto:
            raise ValidationError("Para crear el proyecto es obligatorio indicar el nombre y la referencia.")
        
        # create the project or duplicate one
        values = self._timesheet_create_project_prepare_values()
        if self.product_id.project_template_diseno_id:
            values['name'] = "%s %s" % (self.order_id.ref_proyecto, self.order_id.nombre_proyecto)
            project = self.product_id.project_template_diseno_id.copy(values)
            project.tasks.write({
                'sale_line_id': self.id,
                'partner_id': self.order_id.partner_id.id,
                'email_from': self.order_id.partner_id.email,
                'desde_plantilla': True
            })
            
            project.tasks.filtered(lambda task: task.parent_id != False).write({'sale_line_id': self.id})
        else:
            project = self.env['project.project'].create(values)

        # Avoid new tasks to go to 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create({'name': _('New')})

        # link project as generated by current so line
        self.write({'project_id': project.id})
        
        if self.order_id.seguidor_proyecto_ids:
            project.message_subscribe(partner_ids=self.order_id.seguidor_proyecto_ids.ids)
        
        return project
    
    def _timesheet_create_task(self, project):
        if self.order_id.state == 'draft' and int(self.product_uom_qty) <= 0:
            return False
        
        tasks = self._timesheet_create_task_seleccion(project) + self._timesheet_create_task_individual(project)
        return tasks
    
    def _timesheet_create_task_seleccion(self, project):
        if int(self.product_uom_qty) <= 0:
            return []
        
        task_seleccion = self.env['project.task'].search([
            ('project_id', '=', project.id),
            ('job_id', '=', False),
            ('tarea_seleccion', '=', True),
        ], limit=1)
            
        values = {'sale_line_id': False}
        
        if self.job_id:
            values.update({
                'job_id': self.job_id.id,
                'name': "Seleccionar: %s" % self.job_id.name,
            })
            
        tasks = []
        for i in range(1, int(self.product_uom_qty)):
            if i == 1:
                task = task_seleccion.write(values)
            else:
                task = task_seleccion.copy(values)
            tasks.append(task)
        self.write({'task_id': None})
        return tasks
                
    def _timesheet_create_task_individual(self, project):
        if int(self.product_uom_qty) <= 0 or not self.individual:
            return []
        
        tasks_individual = self.env['project.task'].search([
            ('project_id', '=', project.id),
            ('tarea_individual', '=', True),
        ])
        
        tasks = []
        for task in tasks_individual:
            for i in range(1, int(self.product_uom_qty)):
                new_task = task.copy({'name': task.name})
                tasks.append(new_task)
        self.write({'task_id': None})
        return tasks
    
    def _timesheet_create_task_prepare_values(self, project):
        values = super(SaleOrderLine, self)._timesheet_create_task_prepare_values(project)
        values.update({'job_id': self.job_id.id})
        if self.order_id.state == 'draft' and self.job_id:
            values.update({
                'name': "Selección %s" % self.job_id.name,
                'tarea_seleccion': True,
                'sale_line_id': False
            })
        return values
    
    
class PrevisionFacturacion(models.Model):
    _name = "tetrace.prevision_facturacion"
    _description = "Gestion facturación"
    _order = "fecha desc"
    
    order_id = fields.Many2one("sale.order", string="Pedido Venta")
    order_date_order = fields.Datetime(related="order_id.date_order", store=True)
    order_partner_id = fields.Many2one(related="order_id.partner_id", store=True)
    order_amount_total = fields.Monetary(realted="order_id.partner_id", store=True)
    order_nombre_proyecto = fields.Char(related="order_id.nombre_proyecto", store=True)
    order_project_estado_id = fields.Many2one("tetrace.project_state", 
                                              related="order_id.project_estado_id", store=True)
    fecha = fields.Date('Fecha')
    importe = fields.Monetary("Importe previsto")
    currency_id = fields.Many2one(related='order_id.currency_id')
    facturado = fields.Boolean("Facturado")
    feedbak = fields.Text("Feedbak")
    observaciones = fields.Text("Observaciones")
    importe_factura = fields.Monetary("Importe factura")

