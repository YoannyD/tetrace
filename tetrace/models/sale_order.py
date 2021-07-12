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
    tipo_proyecto_id = fields.Many2one('tetrace.tipo_proyecto', string="Tipo de proyecto", copy=False,
                                       context='{"display_tipo": True}')
    tipo_proyecto_name = fields.Char(related="tipo_proyecto_id.name", string="Nombre Tipo proyecto", store=True)
    num_proyecto = fields.Char('Nº proyecto', copy=False)
    partner_siglas = fields.Char(related="partner_id.siglas")
    tipo_servicio_id = fields.Many2one('tetrace.tipo_servicio', string="Tipo de servicio", copy=False,
                                        domain="[('tipo_proyecto_ids', 'in', tipo_proyecto_id)]")
    proyecto_country_id = fields.Many2one('res.country', string="País", copy=False)
    nombre_proyecto = fields.Char('Nombre proyecto', copy=False)
    detalle_proyecto = fields.Char('Detalle proyecto', copy=False)
    descripcion_proyecto = fields.Char('Descripción proyecto', copy=False, translate=True)
    cabecera_proyecto = fields.Html('Cabecera proyecto', copy=False)
    version_ids = fields.One2many('tetrace.sale_order_version', 'sale_order_id')
    version_count = fields.Integer('Versiones', compute="_compute_version")
    referencia_proyecto_antigua = fields.Char("Ref. proyecto antigua", copy=False)
    coordinador_proyecto_id = fields.Many2one("res.users", string="Coordinador proyecto")
    seguidor_proyecto_ids = fields.Many2many("res.users", string="Seguidores proyecto")
    seguidor_partner_proyecto_ids = fields.Many2many("res.partner", string="Contactos seguidores proyecto",
                                                     compute="_compute_seguidor_partner_proyecto_ids")
    visible_btn_generar_proyecto = fields.Boolean("Visible botón generar proyecto", store=True,
                                                  compute="_compute_visible_btn_generar_proyecto")
    prevision_facturacion_ids = fields.One2many("tetrace.prevision_facturacion", "order_id")
    total_previsto = fields.Monetary("Total previsto", compute="_compute_prevision_facturacion", store=True)
    total_facturado = fields.Monetary("Total facturado (Previsto)", compute="_compute_prevision_facturacion", store=True)
    project_estado_id = fields.Many2one("tetrace.project_state", compute="_compute_project_estado_id",
                                        string="Estado proyecto", store=True)
    rfq = fields.Char("RFQ")
    ref_producto_ids = fields.One2many("tetrace.ref_producto", "order_id")
    imputacion_variable_ids = fields.One2many('tetrace.imputacion_variable', 'order_id')
    total_imputacion_variable = fields.Monetary("Total imputaciones", compute="_compute_total_imputacion_variable")
    estado_tetrace = fields.Selection(selection=[
        ('Pttrealizar', 'Ptt de realizar'),
        ('Rechazado', 'Rechazado'),
        ('descartado', 'Descartado'),
        ('enviado', 'Enviado'),
        ('asignado', 'Asignado'),
        ('Revisado', 'Revisado'),
        ('standby', 'Stand by'),
        ('terminado', 'Terminado'),
    ], string='Estado Tetrace', default='Pttrealizar')
    motivo_cancelacion = fields.Selection(selection=[
        ('precio', 'Valor económico de la propuesta'),
        ('tarde', 'Tardanza en contestar al cliente'),
        ('expectativas', 'No cumple con las expectativas del cliente'), ('nocontesta', 'No contesta'),
    ], string='Motivo Cancelación')
    feedbacktetrace = fields.Text("Feedback")
    importe_pendiente_facturar = fields.Monetary("Total a facturar", compute="_compute_amt_to_invoice")
    importe_total_facturado = fields.Monetary("Total facturado ", compute="_compute_amt_to_invoice")
    purchase_order_count = fields.Integer("Pedidos de Compra", compute="_compute_purchase_order_count")
    invoice_total = fields.Monetary("Total facturado", compute="_compute_invoice_total")
    visible_btn_change_partner = fields.Boolean("Mostrar botón cambiar cliente", store=True,
                                                compute="_compute_visible_btn_change_partner")
    company_coordinador_id = fields.Many2one('res.company', string="Compañia coordinadora", 
                                             default=lambda self: self.env.company)
    prevision_facturacion = fields.Boolean("Generada previsión facturación")
    asignar_cuenta_analitica_manual = fields.Boolean("Asignar cuenta analítica existente")

    sql_constraints = [
        ('ref_proyecto_uniq', 'check(1=1)', "No error")
    ]

    @api.constrains("num_proyecto")
    def _check_num_proyecto(self):
        for r in self:
            if r.num_proyecto:
                if len(r.num_proyecto) != 4:
                    raise ValidationError(_("El Nº de proyecto tiene que ser de 4 caracteres."))

    @api.constrains("estado_tetrace", "motivo_cancelacion", "feedbacktetrace")
    def _check_estado_tetrace(self):
        for r in self:
            if r.estado_tetrace == 'Rechazado' and (not r.motivo_cancelacion or not r.feedbacktetrace):
                raise ValidationError(_("El Motivo de cancelación y Feedback son obligatorios"))

    @api.constrains("referencia_proyecto_antigua")
    def _check_referencia_proyecto_antigua(self):
        for r in self:
            if r.referencia_proyecto_antigua and re.fullmatch(r'\d{4}\.\d{4}', r.referencia_proyecto_antigua) == None:
                raise ValidationError(_("La referencia de proyecto antigua tiene que seguir el patrón 9999.9999."))

    @api.onchange("asignar_cuenta_analitica_manual")
    def _onchange_asignar_cuenta_analitica_manual(self):
        if not self.asignar_cuenta_analitica_manual:
            self.analytic_account_id = False
                
    @api.depends("order_line.untaxed_amount_to_invoice", "order_line.untaxed_amount_invoiced")
    def _compute_amt_to_invoice(self):
        for r in self:
            pendiente_facturar = 0
            facturado = 0
            for line in r.order_line:
                pendiente_facturar += line.untaxed_amount_to_invoice
                facturado += line.untaxed_amount_invoiced
            r.update({
                'importe_total_facturado': facturado,
                'importe_pendiente_facturar': pendiente_facturar
            })

    @api.depends("invoice_ids", "state", "picking_ids")
    def _compute_visible_btn_change_partner(self):
        for r in self:
            if r.invoice_ids or r.state != 'sale' or r.picking_ids:
                r.visible_btn_change_partner = False 
            else:
                r.visible_btn_change_partner = True 
            
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

    @api.depends("invoice_ids")
    def _compute_invoice_total(self):
        for r in self:
            total = 0
            for invoice in r.invoice_ids:
                total += invoice.amount_total_signed
            r.invoice_total = total
                
    @api.depends("seguidor_proyecto_ids")
    def _compute_seguidor_partner_proyecto_ids(self):
        for r in self:
            partner_seguidores_ids = []
            for user in r.seguidor_proyecto_ids:
                if user.partner_id:
                    partner_seguidores_ids.append(user.partner_id.id)
            r.update({'seguidor_partner_proyecto_ids': [(6, 0, partner_seguidores_ids)]})

    @api.onchange('company_id')
    def _onchange_company_id(self):
        super(SaleOrder, self)._onchange_company_id()
        if self.company_id:
            payment_mode_id = None
            payment_term_id = None
            if self.partner_id:
                partner = self.partner_id.with_context(force_company=self.company_id.id)
                payment_mode_id = partner.customer_payment_mode_id and partner.customer_payment_mode_id.id or False
                payment_term_id = partner.property_payment_term_id and partner.property_payment_term_id.id or False
            self.update({
                'payment_mode_id': payment_mode_id,
                'payment_term_id': payment_term_id
            })
            
    def _compute_purchase_order_count(self):
        for r in self:
            r.purchase_order_count = self.env['purchase.order'].search_count([('origin', 'like', r.name)])

    def _compute_version(self):
        for r in self:
            r.version_count = len(r.version_ids)

    @api.depends("imputacion_variable_ids.coste")
    def _compute_total_imputacion_variable(self):
        for r in self:
            total = 0
            for imputacion in r.imputacion_variable_ids:
                total += imputacion.coste
            r.total_imputacion_variable = total

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

    @api.onchange('company_coordinador_id', 'tipo_proyecto_id')
    def _onchange_company_coordinador_id(self):
        for r in self:
            coordinador_proyecto_id = None
            seguidor_proyecto_ids = []
            
            if r.company_coordinador_id:
                coordinador = self.env["tetrace.coordinador_company"].search([
                    ('company_id', '=', r.company_coordinador_id.id),
                    ('tipo_proyecto_id', '=', r.tipo_proyecto_id.id)
                ], limit=1)
                if coordinador:
                    coordinador_proyecto_id = coordinador.coordinador_id.id
                    seguidor_proyecto_ids = [c.id for c in coordinador.seguidor_ids]
            
            r.update({
                'coordinador_proyecto_id': coordinador_proyecto_id,
                'seguidor_proyecto_ids': [(6, 0, seguidor_proyecto_ids)]
            })
            
    @api.onchange('ejercicio_proyecto', 'tipo_proyecto_id', 'num_proyecto', 'referencia_proyecto_antigua')
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
            vals.update({'ref_proyecto': vals.get('referencia_proyecto_antigua')})

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
                
        if 'company_id' in vals:
            self.actualizar_company_project()

        return res

    def actualizar_company_project(self):
        for r in self:
            company_id = r.company_id.id if r.company_id else None
            for project in r.project_ids:
                project.write({'company_id': company_id})
                project.tasks.write({'company_id': company_id})
                

    def generar_ref_proyecto(self):
        self.ensure_one()
        if self.ejercicio_proyecto and self.tipo_proyecto_id and self.num_proyecto:
            return "P%s%s.%s" % (
            self.ejercicio_proyecto, self.tipo_proyecto_id.tipo if self.tipo_proyecto_id else '', self.num_proyecto)
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

    def _create_analytic_account(self, prefix=None):
        for order in self:
            if not order.asignar_cuenta_analitica_manual:
                analytic = self.env['account.analytic.account'].create(order._prepare_analytic_account_data(prefix))
                order.analytic_account_id = analytic
    
    def _action_confirm(self):
        for order in self:
            order.with_context(no_enviar_email_tareas_asignadas=True).action_generar_proyecto()
        res = super(SaleOrder, self)._action_confirm()
        self.actualizar_datos_proyecto()
        self.send_email_confirm()
        return res

    def send_email_confirm(self):
        partner_ids = []
        for seguidor in self.seguidor_proyecto_ids:
            if seguidor.partner_id and seguidor.partner_id.email:
                partner_ids.append(seguidor.partner_id.id)
                
        if self.coordinador_proyecto_id and self.coordinador_proyecto_id.partner_id and \
            self.coordinador_proyecto_id.partner_id.email:
            partner_ids.append(self.coordinador_proyecto_id.partner_id.id)
        
        template_id = self.env['ir.model.data'].xmlid_to_res_id('sale.mail_template_sale_confirmation', raise_if_not_found=False)
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        
        for partner_id in partner_ids:
            template_copy = template.copy({'partner_to': partner_id})
            template_copy.send_mail(self.id, force_send=True)
            template_copy.unlink()
        
    def action_view_purchase_order(self):
        self.ensure_one()
        return {
            'name': 'Pedidos de Compra',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree, form',
            'views': [
                (self.env.ref('purchase.purchase_order_tree').id, 'tree'),
                (self.env.ref('purchase.purchase_order_form').id, 'form')
            ],
            'view_id': False,
            'target': 'current',
            'domain': [('origin', 'like', self.name)]
        }

    def actualizar_datos_proyecto(self):
        for r in self:
            if r.project_ids:
                if not r.ref_proyecto or not r.nombre_proyecto:
                    raise ValidationError('La referencia y el nombre de proyecto son obligatorios.')

                name = "%s %s" % (r.ref_proyecto, r.nombre_proyecto)
                r.project_ids.write({'name': name})
                if not r.asignar_cuenta_analitica_manual:
                    for p in r.project_ids:
                        if p.analytic_account_id.update_from_sale_order:
                            p.analytic_account_id.write({
                                'name': name,
                                'partner_id': r.partner_id.id,
                                'company_id': None
                            })

    def _prepare_analytic_account_data(self, prefix=None):
        values = super(SaleOrder, self)._prepare_analytic_account_data(prefix) 
        values.update({'company_id': None})
        return values
                        
    def action_crear_version(self):
        self.ensure_one()
        wizard = self.env['tetrace.crear_version'].create({
            'sale_order_id': self.id,
            'version': self.env['tetrace.sale_order_version'].siguiente_version(self.id)
        })
        return wizard.open_wizard()

    def action_generar_proyecto(self):
        self.ensure_one()
        if not self.ref_proyecto or not self.nombre_proyecto:
            raise ValidationError(_("Para crear el proyecto es obligatorio indicar el nombre y la referencia."))

        project = None
        if self.project_ids:
            project = self.project_ids[0]

        # Crear el proyecto con la plantilla diseño del primer producto si aún no hay un proyecto creado
        project_template_diseno_ids = []
        for line in self.order_line.sudo():
            if line.product_id.project_template_diseno_id:
                project_template_diseno_ids.append(line.product_id.project_template_diseno_id.id)
                project = line._timesheet_create_project_diseno()
                break

        if not project:
            return
        
        for line in self.order_line.sudo():
            if line.product_id.project_template_diseno_id and \
                line.product_id.project_template_diseno_id.id not in project_template_diseno_ids:
                template_tasks = self.env['project.task'].sudo().search([
                    ('project_id', '=', line.product_id.project_template_diseno_id.id),
                    ('activada', 'in', [True, False])
                ])
                line.copy_tasks(template_tasks, project, True)
            
            if line.product_id.service_tracking in ['task_in_project', 'task_global_project']:
                line.with_context(tracking_disable=True)._timesheet_create_task_desde_diseno(project)
                
        self.actualizar_datos_proyecto()
        if not self.env.context.get("no_enviar_email_tareas_asignadas"):
            project.enviar_email_tareas_asignadas()

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
            'views': [(view_form_id, 'form'), (view_kanban_id, 'kanban')],
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

    def action_importar_productos(self):
        self.ensure_one()
        wizard = self.env['tetrace.importar_producto_pv'].create({"order_id": self.id})
        return wizard.open_wizard()

    def action_imputar_variables(self):
        self.ensure_one()
        ImputacionLine = self.env["tetrace.imputacion_variable_line"]
        porcentajes_lineas = self.porcentajes_incremeto_imputacion()
        for imputacion in self.imputacion_variable_ids:
            for line_id, porcentaje in porcentajes_lineas.items():
                # Eliminar lineas que ya no existan en el las lineas del pedido de venta
                imputaciones_line_borrar = ImputacionLine.search([
                    ('imputacion_id', '=', imputacion.id),
                    ('order_line_id', 'not in', self.order_line.ids)
                ])
                imputaciones_line_borrar.unlink()

                imputacion_line = ImputacionLine.search([
                    ('imputacion_id', '=', imputacion.id),
                    ('order_line_id', '=', int(line_id))
                ], limit=1)
                incremento_antiguo = imputacion_line.incremento if imputacion_line else 0

                line = self.env['sale.order.line'].search([('id', '=', int(line_id))], limit=1)
                incremento = (imputacion.coste * porcentaje) / 100
                if imputacion_line:
                    imputacion_line.write({
                        'incremento': incremento,
                        'porcentaje': porcentaje
                    })
                else:
                    imputacion_line = ImputacionLine.create({
                        'imputacion_id': imputacion.id,
                        'order_line_id': int(line_id),
                        'incremento': incremento,
                        'porcentaje': porcentaje
                    })

                if imputacion_line.order_line_id.product_uom_qty:
                    incremento_price_unit = incremento / imputacion_line.order_line_id.product_uom_qty
                else:
                    incremento_price_unit = incremento

                line.write({'price_unit': line.price_unit + incremento_price_unit - incremento_antiguo})

    def action_change_partner(self):
        self.ensure_one()
        wizard = self.env['tetrace.change_partner_sale_order'].create({'order_id': self.id})
        return wizard.open_wizard()
                
    def porcentajes_incremeto_imputacion(self):
        self.ensure_one()
        total = 0
        for line in self.order_line:
            total += line.price_subtotal

        porcentajes = {}
        for line in self.order_line:
            porcentaje_linea = (100 * line.price_subtotal) / total if total else 0
            porcentajes.update({str(line.id): porcentaje_linea})

        return porcentajes


class RefProducto(models.Model):
    _name = "tetrace.ref_producto"
    _description = "Referencias fuera de catalogo"

    name = fields.Char("Referencia")
    order_id = fields.Many2one("sale.order", string="Pedido de venta")
    cantidad = fields.Float("Cantidad")

