# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import re
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
    seguidor_proyecto_ids = fields.Many2many("res.partner", string="Seguidores proyecto")

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
                    
    def _compute_version(self):
        for r in self:
            r.version_count = len(r.version_ids)

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
            or 'referencia_proyecto_antigua' in vals:
            self.actualizar_datos_proyecto()

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
        return res

    def actualizar_datos_proyecto(self):
        for r in self:
            if r.project_ids:
                if not r.ref_proyecto or not r.nombre_proyecto:
                    raise ValidationError('La referencia y el nombre de proyecto son obligatorios.')
                name = "%s %s" % (r.ref_proyecto, r.nombre_proyecto)
                r.project_ids.write({'name': name})
                for p in r.project_ids:
                    p.analytic_account_id.write({'name': r.ref_proyecto})

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
            raise ValidationError("Para crear el proyecto es obligatorio indicar el nombre y la referencia.")
        
        project = None
        for line in self.order_line:
            if line.product_id and line.product_id.project_template_diseno_id:
                if not project:
                    project = line._timesheet_create_project_diseno()
                line._timesheet_create_task(project)
                      

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_project_prepare_values(self):
        values = super(SaleOrderLine, self)._timesheet_create_project_prepare_values()
        if self.order_id.coordinador_proyecto_id:
            values.update({
                'user_id': self.order_id.coordinador_proyecto_id.id
            })
        return values
    
    def _timesheet_create_project(self):
        self.ensure_one()
        if not self.order_id.ref_proyecto or not self.order_id.nombre_proyecto:
            raise ValidationError("Para crear el proyecto es obligatorio indicar el nombre y la referencia.")

        project = super(SaleOrderLine, self)._timesheet_create_project()
        values = {
            "name": "%s %s" % (self.order_id.ref_proyecto, self.order_id.nombre_proyecto)
        }
        project.write(values)

        if self.order_id.seguidor_proyecto_ids:
            project.with_context(add_followers=True).message_subscribe(partner_ids=self.order_id.seguidor_proyecto_ids.ids)
        
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
            })
            # duplicating a project doesn't set the SO on sub-tasks
            project.tasks.filtered(lambda task: task.parent_id != False).write({
                'sale_line_id': self.id,
            })
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
