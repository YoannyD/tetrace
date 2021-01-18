# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _, tools

_logger = logging.getLogger(__name__)


class Viaje(models.Model):
    _name = 'tetrace.viaje'
    _description = "Viajes"
    
    name = fields.Char("Nombre", compute="_compute_name", store="True")
    fecha = fields.Date("Fecha")
    origen = fields.Char("Origen", translate=True)
    destino = fields.Char("Destino", translate=True)
    contratado = fields.Boolean("Contratado")
    realizado = fields.Boolean("Realizado")
    employee_id = fields.Many2one("hr.employee", string="Persona")
    task_id = fields.Many2one("project.task", string="Tarea")
    observaciones = fields.Text("Observaciones", translate=True)
    
    @api.depends("fecha", "origen", "destino")
    def _compute_name(self):
        for r in self:
            name = ""
            if r.fecha:
                name += "%s " % fields.Date.to_string(r.fecha)
            
            if name:
                name += " - "
            name += " %s - %s" % (r.origen, r.destino)
            r.name = name
    
    @api.model
    def create(self, vals):
        res = super(Viaje, self).create(vals)
        res.notificar_a_seguidores()
        res.pasar_tarea_a_en_proceso()
        return res
    
    def pasar_tarea_a_en_proceso(self):
        for r in self:
            if not r.task_id or not r.task_id.project_id:
                continue
                
            # Obtener etapa en proceso
            stage = self.env['project.task.type'].search([
                ('project_ids', 'in', [r.task_id.project_id.id]),
                ('id', '=', 10)
            ])
            if not stage:
                continue
            
            if r.task_id.stage_id.id != stage.id:
                r.task_id.write({'stage_id': stage.id})
    
    def notificar_a_seguidores(self):
        email_tmpl = self.env.ref('tetrace.email_template_notificar_nuevo_viaje')
        
        for r in self:
            if not r.employee_id or not r.employee_id.work_email:
                continue
            mail = self.env['mail.template'].with_context(email_to=r.employee_id.work_email).browse(email_tmpl.id)
            mail.send_mail(r.id, force_send=True)
            