# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

OPCIONES_DESACTIVACION = [
    ('viaje', _('Viaje')),
    ('baja', _('Baja')),
    ('informatica', _('Informática')),
    ('equipos', _('Equipos')),
    ('reubicacion', _('Reubicación')),
    ('facturacion', _('Facturación')),
]


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def _default_sale_line_id(self):
        return False

    tarea_seleccion = fields.Boolean("Tarea Selección")
    job_id = fields.Many2one('hr.job', string="Puesto de trabajo")
    entrega_ids = fields.One2many('project.task.entrega', 'task_id')
    entrega_total = fields.Float('Total entrega', compute="_compute_entrega_total")
    producto_entrega = fields.Boolean(related="sale_line_id.product_entregado")
    desde_plantilla = fields.Boolean("Creada desde plantilla")
    tipo = fields.Selection([
        ('activacion', _('Activación')),
        ('desactivacion', _('Desactivacion'))
    ], string="Tipo tarea")
    tarea_individual = fields.Boolean("Individual")
    viajes = fields.Boolean("Trips")
    viaje_ids = fields.One2many("tetrace.viaje", "task_id")
    activada = fields.Boolean("Activada", default=True)
    opciones_desactivacion = fields.Selection(OPCIONES_DESACTIVACION, string="Desactivación")
    sale_line_id = fields.Many2one('sale.order.line', default=_default_sale_line_id)
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    deadline = fields.Integer("Deadline ")
    alquiler_vehiculo_ids = fields.One2many("tetrace.alquiler_vehiculo", "task_id")
    alojamiento_ids = fields.One2many("tetrace.alojamiento", "task_id")
    ref_individual = fields.Char("Referencia individual")
    department_id = fields.Many2one("hr.department", string="Departamento")
    department_laboral = fields.Boolean(related="department_id.laboral")
    info_puesto_id = fields.Many2one('ir.attachment', string='Información puesto',
                                     domain=[('res_model', '=', 'project.task')])
    ref_created = fields.Char("Referencia creación", copy=False, help="Compuesto por project_id-task_id de origen")
    notify_by_email = fields.Boolean("Notificado por email")
    asginacion_ids = fields.One2many('tetrace.asignacion', 'task_id')
    project_id_sale_order_id = fields.Many2one("sale.order", related="project_id.sale_order_id", string="Pedido de venta (Proyecto)")
    ausencia = fields.Boolean("Ausencia")
    ausencia_ids = fields.One2many('tetrace.ausencia', 'task_id', string="Ausencias")
    busqueda_perfiles = fields.Boolean("Búsqueda perfiles")
    proyecto_necesidad_count = fields.Integer("Nª Necesidades", compute="_compute_proyecto_necesidad")

    def _compute_proyecto_necesidad(self):
        for r in self:
            r.proyecto_necesidad_count = len(r.project_id.proyecto_necesidad_ids)
    
    @api.constrains('tarea_individual', 'tarea_seleccion', 'tipo')
    def _check_tipos_tareas(self):
        for r in self:
            if r.tarea_seleccion and not r.tarea_individual:
                raise ValidationError(_("Si es tarea de selección tiene que ser tarea individual"))

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
                body = _("<strong>Entrega:</strong><br/>Cantidad entregada %s -> %s") % (
                entregas[str(r.id)]['total'], r.entrega_total)
                r.message_post(body=body, subject="Entrega")

        if 'info_puesto_id' in vals and not self.env.context.get("no_actualizar_info_puesto"):
            self.actualizar_info_puesto()

        if ('employee_id' in vals or 'job_id' in vals) and not self.env.context.get("no_actualizar_empleado"):
            self.actualizar_tareas_individuales()

        return res

    def actualizar_tareas_individuales(self):
        for r in self:
            if not r.tarea_individual or not r.ref_individual:
                continue

            tasks = self.env['project.task'].search([
                ('project_id', '=', r.project_id.id),
                ('tarea_individual', '=', True),
                ('ref_individual', '=', r.ref_individual),
                ('activada', 'in', [True, False])
            ])

            for task in tasks:
                values = {'job_id': r.job_id.id}
                if r.employee_id:
                    pos1 = task.name.find("(")
                    pos2 = task.name.find(")")
                    if pos1 >= 0 and pos2 >= 0:
                        cadena_a_reemplazar = task.name[pos1 + 1:pos2]
                        name = task.name.replace(cadena_a_reemplazar, r.employee_id.name)
                    else:
                        name = "%s (%s)" % (task.name, r.employee_id.name)

                    values.update({
                        'name': name,
                        'employee_id': r.employee_id.id,
                    })
                task.with_context(no_actualizar_empleado=True).update(values)

    def actualizar_info_puesto(self):
        for r in self:
            if r.department_id and r.ref_individual:
                task = self.search([
                    ('ref_individual', '=', r.ref_individual),
                    ('activada', 'in', [True, False]),
                    ('project_id', '=', r.project_id.id),
                    ('department_id', '=', r.department_id.id)
                ])
                task.with_context(no_actualizar_info_puesto=True).update({'info_puesto_id': r.info_puesto_id.id})

    @api.model
    def _where_calc(self, domain, active_test=True):
        if 'activada' in self._fields and active_test and self._context.get('active_test', True):
            if not any(item[0] == 'activada' for item in domain):
                domain = [('activada', '=', 1)] + domain
        return super(ProjectTask, self)._where_calc(domain, active_test)

    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        if self.env.context.get("default_res_model") == 'project.project' or self.env.context.get("no_notify"):
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
    
    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        if self.env.context.get("no_notificar"):
            return []
        return super(ProjectTask, self)._message_auto_subscribe_followers(updated_values, default_subtype_ids)

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
    
    @api.model
    def check_task_exist(self, ref_created, ref_individual=None):
        domain = [('ref_created', '=', ref_created)]
        if ref_individual:
            domain += [('ref_individual', '=', ref_individual)]
        task_count = self.search_count(domain)
        return True if task_count > 0 else False
    
    def get_responsable_y_seguidores(self):
        self.ensure_one()
        seguidores_ids = []
        responsable_id = None
        asignaciones = self.asginacion_ids.filtered(lambda x: x.company_id.id == self.env.company.id)   
        if asignaciones:
            for asignacion in asignaciones:
                for seguidor in asignacion.seguidor_ids.filtered(lambda x: x.partner_id):
                    seguidores_ids.append(seguidor.partner_id.id)
                if asignacion.responsable_id:
                    responsable_id = asignacion.responsable_id.id
        return responsable_id, seguidores_ids

    def view_proyecto_necesidad_action(self):
        self.ensure_one()
        action = self.env.ref("tetrace.tetrace_proyecto_necesidad_action").read()[0]
        action.update({'domain': [('project_id', '=', self.project_id.id)]})
        return action
    
    def create_activity_viaje(self, summary, fecha=None):
        values = {
            'summary': summary,
            'activity_type_id': self.env.ref("mail.mail_activity_data_todo").id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'project.task')], limit=1).id,
            'res_id': self.id,
            'user_id': self.user_id.id
        }
        
        if fecha:
            values.update({'date_deadline': fecha - timedelta(days=5)})
            
        self.env['mail.activity'].create(values)

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    bloquear_imputar_tiempos = fields.Boolean('Bloquear imputación de tiempos')
    no_update_deadline = fields.Boolean("No actualizar la fecha límite")


class ProjectTaskEntrega(models.Model):
    _name = 'project.task.entrega'
    _description = "Entregas (Tareas)"

    name = fields.Char("Observaciones", translate=True)
    fecha = fields.Date("Fecha")
    entregado = fields.Float("Entregado")
    task_id = fields.Many2one("project.task")
