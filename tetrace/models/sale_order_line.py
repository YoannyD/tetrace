# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    no_imprimir = fields.Boolean("Archivado")
    product_entregado = fields.Boolean(related="product_id.producto_entrega")
    individual = fields.Boolean("Individual")
    imputacion_variable_line_ids = fields.One2many('tetrace.imputacion_variable_line', 'order_line_id')
    product_quantity = fields.Float('Cantidad a mano', compute='_compute_product_quantity')
    product_purchase = fields.Float('Comprado', compute='_compute_stock_quantity')
    product_stock = fields.Float('Recepcionado', compute='_compute_stock_quantity')

    def _compute_stock_quantity(self):
        for line in self:
            purchase = 0
            stock = 0
            if line.product_id:
                move_lines = self.env['stock.move.line'].search([('product_id', '=', line.product_id.id)])
                for move in move_lines:
                    if move.location_id.usage == 'supplier' and move.location_dest_id.usage == 'internal':
                        purchase += move.qty_done
                        stock += move.qty_done
            line.product_purchase = purchase
            line.product_stock = stock


    def _compute_product_quantity(self):
        for line in self:
            qty_available = 0
            if line.product_id:
                qty_available = line.product_id.qty_available
            line.product_quantity = qty_available


    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        self.update({
            'individual': self.product_id.individual,
            'no_imprimir': self.product_id.archivar_order_line,
        })
        return super(SaleOrderLine, self).product_id_change()

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        return

#     def write(self, vals):
#         res = super(SaleOrderLine, self).write(vals)
#         if "price_unit" in vals:
#             for r in self:
#                 r.imputacion_variable_line_ids.unlink()
#         return res
    
    def _timesheet_service_generation(self):
        self = self.sudo().with_context(no_notificar=True)
        project_sale = []
        for r in self:
            if r.order_id.project_ids:
                project_sale.append(r.order_id.id)
        
        super(SaleOrderLine, self)._timesheet_service_generation()

        project_template_ids = []
        for r in self:
            project_template = r.product_id.with_context(force_company=1).project_template_id
            if r.order_id.project_ids and project_template and r.order_id.id in project_sale and \
                project_template.id not in project_template_ids:
                project_template_ids.append(project_template.id)
                project_tasks = self.env['project.task'].sudo().search([
                    ('project_id', '=', project_template.id),
                    ('activada', 'in', [True, False]),
                ])
                self.create_new_tasks_from_template(project_tasks, r.order_id.project_ids[0], False)

            r.actualizar_tareas_individuales()
            r.actualizar_info_puesto()

    def actualizar_tareas_individuales(self):
        self.ensure_one()
        if self.order_id.project_ids:
            tasks_individuales_plantilla = self.env['project.task'].search([
                ('project_id', '=', self.order_id.project_ids[0].id),
                ('tarea_individual', '=', True),
                ('desde_plantilla', '=', True),
                ('activada', 'in', [True, False]),
                ('ref_individual', '!=', False)
            ])
            tasks_individuales_plantilla.actualizar_tareas_individuales()

    def actualizar_info_puesto(self):
        self.ensure_one()
        if self.order_id.project_ids:
            tasks_departamento_plantilla = self.env['project.task'].search([
                ('project_id', '=', self.order_id.project_ids[0].id),
                ('department_id', '!=', False),
                ('desde_plantilla', '=', True),
                ('activada', 'in', [True, False]),
                ('ref_individual', '!=', False)
            ])
            tasks_departamento_plantilla.actualizar_info_puesto()

    def validar_crear_proyecto(self):
        if not self.order_id.ref_proyecto or not self.order_id.nombre_proyecto:
            raise ValidationError(_("Para crear el proyecto es obligatorio indicar el nombre y la referencia."))
            
    def _timesheet_create_project_prepare_values(self):
        values = super(SaleOrderLine, self)._timesheet_create_project_prepare_values()
        values.update({
            "name": "%s %s" % (self.order_id.ref_proyecto, self.order_id.nombre_proyecto),
            "tasks": None,
            "company_id": self.order_id.company_id.id or self.env.company.id,
            'user_id': self.order_id.coordinador_proyecto_id.id,
            'company_coordinador_id': self.order_id.company_coordinador_id.id
        })
        return values

    def _timesheet_create_project(self):
        self = self.sudo().with_context(no_notificar=True)
        self.validar_crear_proyecto()

        if self.order_id.project_ids:
            project_tasks = self.env['project.task'].search([
                ('project_id', '=', self.product_id.project_template_id.id),
                ('activada', 'in', [True, False]),
            ])
            self.create_new_tasks_from_template(project_tasks, self.order_id.project_ids[0], False)
            return self.order_id.project_ids[0]

        values = self._timesheet_create_project_prepare_values()
        project_template = self.product_id.with_context(force_company=1).project_template_id
        if project_template:
            project = project_template.copy(values)
            project_tasks = self.env['project.task'].search([
                ('project_id', '=', project_template.id),
                ('activada', 'in', [True, False]),
            ])
            self.create_new_tasks_from_template(project_tasks, project, False)
        else:
            project = self.env['project.project'].create(values)

        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create({'name': _('New')})

        self.write({'project_id': project.id})

        if project.user_id and project.user_id.partner_id:
            project.with_context(add_follower=True).message_subscribe(partner_ids=[project.user_id.partner_id.id])

        return project

    def create_new_tasks_from_template(self, tasks, project, desde_plantilla=False):
        tasks_with_sale_line = project.tasks.filtered(lambda t: t.sale_line_id).ids
        new_tasks = self.copy_tasks(tasks, project, desde_plantilla)
        self.project_id.tasks \
            .filtered(lambda task: task.id not in tasks_with_sale_line and task.parent_id != False) \
            .write({'sale_line_id': None})
        return new_tasks
    
    def _timesheet_create_project_diseno(self):
        self.validar_crear_proyecto()

        if self.project_id:
            self.create_new_tasks_from_template(self.product_id.project_template_diseno_id.tasks, self.project_id, True)
            return self.project_id

        values = self._timesheet_create_project_prepare_values()
        if self.product_id.project_template_diseno_id:
            project = self.product_id.project_template_diseno_id.copy(values)
            template_tasks = self.env['project.task'].sudo().search([
                ('project_id', '=', self.product_id.project_template_diseno_id.id),
                ('activada', 'in', [True, False])
            ])
            self.create_new_tasks_from_template(template_tasks, project, True)
        else:
            project = self.env['project.project'].create(values)

        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create({'name': _('New')})

        self.write({'project_id': project.id})

        _logger.warning(project.user_id.partner_id)
        if project.user_id and project.user_id.partner_id:
            project.with_context(add_follower=True).message_subscribe(partner_ids=[project.user_id.partner_id.id])
        
        return project

    def _timesheet_create_task(self, project):
        task = self.existe_tarea_rel_linea(project)
        if not task:
            task = super(SaleOrderLine, self)._timesheet_create_task(project)
        self._timesheet_create_task_individual(project)
        return task

    def _timesheet_create_task_desde_diseno(self, project):
        if self.existe_tarea_rel_linea(project) or \
            (self.order_id.state == 'draft' and int(self.product_uom_qty) <= 0):
            return []

        return self._timesheet_create_task_individual(project, True)

    def _timesheet_create_task_individual(self, project, desde_plantilla=False):
        if int(self.product_uom_qty) <= 0 or not self.individual:
            return []

        domain = [
            ('tarea_individual', '=', True),
            ('activada', 'in', [True, False])
        ]
        if desde_plantilla:
            domain += [('project_id', '=', self.product_id.project_template_diseno_id.id)]
        else:
            domain += [('project_id', '=', self.product_id.with_context(force_company=1).project_template_id.id)]

        tasks_individual = self.env['project.task'].sudo().search(domain)

        tasks = []
        for task in tasks_individual:
            if task.employee_id:
                name = "%s (%s)" % (task.name, task.employee_id.name)
            else:
                name = task.name

            for i in range(0, int(self.product_uom_qty)):
                ref_individual = "%s-%s" % (self.id, i)
                ref_created = "%s-%s-%s" % (self.order_id.id, task.project_id.id, task.id)
                if task.check_task_exist(ref_created, ref_individual):
                    break
                
                values = {
                    'name': name,
                    'partner_id': self.order_id.partner_id.id,
                    'company_coordinador_id': self.order_id.company_coordinador_id.id,
                    'job_id': self.job_id.id,
                    'project_id': project.id,
                    'ref_individual': "%s-%s" % (self.id, i),
                    'desde_plantilla': desde_plantilla,
                    "company_id": self.order_id.company_id.id or self.env.company.id,
                    'ref_created': ref_created,
                }
                
                responsable_id, seguidores_ids = task.get_responsable_y_seguidores(self.order_id.company_coordinador_id) 
                if responsable_id:
                    values.update({'user_id': responsable_id})
                
                new_task = task.with_context(mail_notrack=True).copy(values)
                if seguidores_ids:
                    new_task.with_context(add_follower=True).message_subscribe(seguidores_ids, [])
                tasks.append(new_task)
        self.write({'task_id': None})
        return tasks

    def copy_tasks(self, tasks, project=None, desde_plantilla=False):
        new_tasks = []
        for task in tasks:
            ref_created = "%s-%s-%s" % (self.order_id.id, task.project_id.id, task.id)
            if task.check_task_exist(ref_created) or task.tarea_individual:
                continue

            responsable_id, seguidores_ids = task.get_responsable_y_seguidores(self.order_id.company_coordinador_id)   
            new_task = task.with_context(tracking_disable=True).copy({
                'name': task.name,
                'project_id': project.id if project else task.project_id.id,
                'sale_line_id': None,
                'partner_id': self.order_id.partner_id.id,
                'email_from': self.order_id.partner_id.email,
                'company_coordinador_id': self.order_id.company_coordinador_id.id,
                'desde_plantilla': desde_plantilla,
                "company_id": self.order_id.company_id.id or self.env.company.id,
                'ref_created': ref_created,
                'user_id': responsable_id
            })
            if seguidores_ids:
                new_task.with_context(add_follower=True).message_subscribe(seguidores_ids, [])
            new_tasks.append(new_task)
            
        return new_tasks

    def existe_tarea_rel_linea(self, project):
        self.ensure_one()
        task = self.env['project.task'].sudo().search([
            ('project_id', '=', project.id),
            ('sale_line_id', '=', self.id),
            ('activada', 'in', [True, False]),
        ], limit=1)
        return task
    