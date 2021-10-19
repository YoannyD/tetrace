# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"
    
    enlace = fields.Char("Enlace")
    bloqueado = fields.Boolean("Bloqueado")
    fecha_limite = fields.Date("Fecha límite")
    confirmado = fields.Boolean("Confirmado por usuario", readonly=True)
    project_id = fields.Many2one("project.project", string="Proyecto")
    fecha_resuelto = fields.Date("Fecha resuelto", readonly=True)
    fecha_validado = fields.Date("Fecha validado", readonly=True)
    fecha_previsto = fields.Date("Fecha previsto", readonly=True)
    dias_totales = fields.Integer("Días totales", compute="_compute_dias_totales")
    priority = fields.Selection(selection_add=[('4', 'Muy urgente'), ('5', 'Prioritario')])
    current_user_id = fields.Many2one("res.user", string="Usuario actual", 
                                      compute="_compute_current_user")
    current_user_user = fields.Boolean("Usuario actual permiso usuario",
                                      compute="_compute_current_user")
    current_user_manager = fields.Boolean("Usuario actual permiso administrador",
                                          compute="_compute_current_user")
    
    def _compute_current_user(self):
        for r in self:
            user = False
            manager = False
            if self.env.user.has_group("helpdesk.group_helpdesk_manager"):
                manager = True
            elif self.env.user.has_group("helpdesk.group_helpdesk_user"):
                user = True
            
            r.update({
                'current_user_id': self.env.uid,
                'current_user_user': user,
                'current_user_manager': manager,
            })
    
    @api.depends("fecha_validado")
    def _compute_dias_totales(self):
        for r in self:
            dias = 0
            if r.fecha_validado and r.create_date:
                dias = (r.fecha_validado - r.create_date.date()).days
            r.dias_totales = dias
    
    @api.model
    def create(self, vals):
        res = super(HelpdeskTicket, self).create(vals)
        res.cambio_etapa()
        return res
    
    def write(self, vals):
        res = super(HelpdeskTicket, self).write(vals) 
        if 'stage_id' in vals:
            self.cambio_etapa()
        return res
    
    def cambio_etapa(self):
        for r in self:
            if r.stage_id:
                if r.stage_id.validado:
                    r.write({
                        'confirmado': True,
                        'fecha_validado': fields.Date.today()
                    })
                elif r.stage_id.resuelto:
                    r.write({'fecha_resuelto': fields.Date.today()})