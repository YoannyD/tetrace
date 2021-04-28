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

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        self.individual = self.product_id.individual
        return super(SaleOrderLine, self).product_id_change()

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        return

    def _timesheet_service_generation(self):
        self = self.sudo()
        project_sale = []
        for r in self:
            if r.order_id.project_ids:
                project_sale.append(r.order_id.id)

        super(SaleOrderLine, self.sudo())._timesheet_service_generation()

        project_template_ids = []
        for r in self.sudo():
            project_template = r.product_id.with_context(force_company=1).project_template_id
            if r.product_id.service_tracking == 'task_in_project' and r.order_id.project_ids and \
                project_template and r.order_id.id in project_sale and \
                project_template.id not in project_template_ids:
                project_template_ids.append(project_template.id)
                template_tasks = self.env['project.task'].sudo().search([
                    ('project_id', '=', project_template.id),
                    ('activada', 'in', [True, False]),
                ])

                for task in template_tasks:
                    if task.check_task_exist(self.order_id.id, task.project_id.id, task.id) or task.tarea_individual:
                        continue

                    new_task = task.copy({
                        'name': task.name,
                        'project_id': r.order_id.project_ids[0].id,
                        "company_id": self.env.company.id,
                        'sale_line_id': None,
                        'partner_id': r.order_id.partner_id.id,
                        'email_from': r.order_id.partner_id.email,
                        'ref_created': "%s-%s-%s" % (self.order_id.id, task.project_id.id, task.id)
                    })

                    if task.message_partner_ids:
                        new_task.with_context(add_follower=True).message_subscribe(task.message_partner_ids.ids, [])
                        new_task.notificar_asignacion_seguidores()

        if r.order_id.project_ids:
            tasks_individuales_plantilla = self.env['project.task'].search([
                ('project_id', '=', r.order_id.project_ids[0].id),
                ('tarea_individual', '=', True),
                ('desde_plantilla', '=', True),
                ('activada', 'in', [True, False]),
                ('ref_individual', '!=', False)
            ])
            tasks_individuales_plantilla.actualizar_tareas_individuales()

            tasks_departamento_plantilla = self.env['project.task'].search([
                ('project_id', '=', r.order_id.project_ids[0].id),
                ('department_id', '!=', False),
                ('desde_plantilla', '=', True),
                ('activada', 'in', [True, False]),
                ('ref_individual', '!=', False)
            ])
            tasks_departamento_plantilla.actualizar_info_puesto()

    def _timesheet_create_project_prepare_values(self):
        values = super(SaleOrderLine, self)._timesheet_create_project_prepare_values()
        values.update({'user_id': self.order_id.coordinador_proyecto_id.id})
        return values

    def _timesheet_create_project(self):
        self.ensure_one()
        self = self.sudo()
        if not self.order_id.ref_proyecto or not self.order_id.nombre_proyecto:
            raise ValidationError(_("Para crear el proyecto es obligatorio indicar el nombre y la referencia."))

        if self.order_id.project_ids and self.product_id.service_tracking in ['task_global_project', 'task_in_project']:
            return self.order_id.project_ids[0]

        values = self._timesheet_create_project_prepare_values()
        project_template = self.product_id.with_context(force_company=1).project_template_id
        if project_template:
            values.update({
                "name": "%s %s" % (self.order_id.ref_proyecto, self.order_id.nombre_proyecto),
                "tasks": None,
                "company_id": self.env.company.id
            })
            project = project_template.copy(values)
            project_tasks = self.env['project.task'].search([
                ('project_id', '=', project_template.id),
                ('activada', 'in', [True, False]),
            ])
            for task in project_tasks:
                if task.check_task_exist(self.order_id.id, task.project_id.id, task.id) or task.tarea_individual:
                    continue

                new_task = task.copy({
                    'name': task.name,
                    'sale_line_id': None,
                    'partner_id': self.order_id.partner_id.id,
                    'email_from': self.order_id.partner_id.email,
                    'project_id': project.id,
                    "company_id": self.env.company.id,
                    'ref_created': "%s-%s-%s" % (self.order_id.id, task.project_id.id, task.id)
                })

                if task.message_partner_ids:
                    new_task.with_context(add_follower=True).message_subscribe(task.message_partner_ids.ids, [])
                    new_task.notificar_asignacion_seguidores()
        else:
            project = self.env['project.project'].create(values)

        # Avoid new tasks to go to 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create({'name': _('New')})

        # link project as generated by current so line
        self.write({'project_id': project.id})

        if self.order_id.seguidor_partner_proyecto_ids:
            project.with_context(add_follower=True).message_subscribe(self.order_id.seguidor_partner_proyecto_ids.ids, [])

        return project

    def _timesheet_create_project_diseno(self):
        self.ensure_one()
        if not self.order_id.ref_proyecto or not self.order_id.nombre_proyecto:
            raise ValidationError(_("Para crear el proyecto es obligatorio indicar el nombre y la referencia."))

        project_follower_ids = self.order_id.seguidor_partner_proyecto_ids.ids
        # create the project or duplicate one
        values = self._timesheet_create_project_prepare_values()
        if self.product_id.project_template_diseno_id:
            values.update({
                "name": "%s %s" % (self.order_id.ref_proyecto, self.order_id.nombre_proyecto),
                "tasks": None,
                "company_id": self.env.company.id
            })

            project_follower_ids += self.product_id.project_template_diseno_id.message_partner_ids.ids
            project = self.product_id.project_template_diseno_id.copy(values)
            for task in self.product_id.project_template_diseno_id.tasks:
                if task.check_task_exist(self.order_id.id, task.project_id.id, task.id) or task.tarea_individual:
                    continue

                new_task = task.copy({
                    'name': task.name,
                    'sale_line_id': None,
                    'partner_id': self.order_id.partner_id.id,
                    'email_from': self.order_id.partner_id.email,
                    'desde_plantilla': True,
                    'project_id': project.id,
                    "company_id": self.env.company.id,
                    'ref_created': "%s-%s-%s" % (self.order_id.id, task.project_id.id, task.id)
                })

                if task.message_partner_ids:
                    new_task.with_context(add_follower=True).message_subscribe(task.message_partner_ids.ids, [])
                    new_task.notificar_asignacion_seguidores()

            project.tasks.filtered(lambda task: task.parent_id != False).write({'sale_line_id': None})
        else:
            project = self.env['project.project'].create(values)

        # Avoid new tasks to go to 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create({'name': _('New')})

        # link project as generated by current so line
        self.write({'project_id': project.id})

        if project_follower_ids:
            project.with_context(add_follower=True).message_subscribe(project_follower_ids, [])

        return project

    def _timesheet_create_task(self, project):
        task = self.env['project.task'].search([
            ('project_id', '=', project.id),
            ('sale_line_id', '=', self.id),
        ], limit=1)
        if not task:
            task = super(SaleOrderLine, self)._timesheet_create_task(project)
        self._timesheet_create_task_individual(project)
        return task

    def _timesheet_create_task_desde_diseno(self, project):
        if self.order_id.state == 'draft' and int(self.product_uom_qty) <= 0:
            return False

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
            if self.job_id:
                name = "%s (%s)" % (task.name, self.job_id.name)
            else:
                name = task.name

            for i in range(0, int(self.product_uom_qty)):
                if task.check_task_exist(self.order_id.id, task.project_id.id, task.id, int(self.product_uom_qty)):
                    break
                
                new_task = task.copy({
                    'name': name,
                    'partner_id': self.order_id.partner_id.id,
                    'job_id': self.job_id.id,
                    'project_id': project.id,
                    'ref_individual': "%s-%s" % (self.id, i),
                    'desde_plantilla': desde_plantilla,
                    "company_id": self.env.company.id,
                    'ref_created': "%s-%s-%s" % (self.order_id.id, task.project_id.id, task.id)
                })
                tasks.append(new_task)
        self.write({'task_id': None})
        return tasks