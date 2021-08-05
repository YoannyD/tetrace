# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _, tools
from datetime import timedelta

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
    employee_active_ids = fields.Many2many("hr.employee", related="task_id.project_id.tecnico_ids")
    task_id = fields.Many2one("project.task", string="Tarea")
    observaciones = fields.Text("Observaciones", translate=True)
    pcr = fields.Boolean("PCR")
    
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
        if vals.get("pcr"):
            res.create_pcr()
        res.pasar_tarea_a_en_proceso()
        res.create_task_activity("create")
        return res
    
    def write(self, vals):
        res = super(Viaje, self).write(vals)
        if vals.get("pcr"):
            self.create_pcr()
        self.create_task_activity("update")
        return res
    
    def create_pcr(self):
        PCR = self.env['tetrace.pcr']
        for r in self:
            if r.pcr:
                tasks_pcr = self.env['project.task'].search([
                    ('project_id', '=', r.task_id.project_id.id),
                    ('pcr', '=', True)
                ])
                
                for t_pcr in tasks_pcr:
                    pcr = PCR.search([
                        ('task_id', '=', t_pcr.id),
                        ('fecha', '=', r.fecha),
                        ('ubiacion', '=', r.destino),
                        ('employee_id', '=', r.employee_id.id),
                    ], limit=1)
                    if not pcr:
                        PCR.create({
                            'task_id': t_pcr.id,
                            'fecha': r.fecha,
                            'ubiacion': r.destino,
                            'employee_id': r.employee_id.id,
                        })
    
    def create_task_activity(self, accion):
        for r in self:
            if not r.task_id or (accion == "update" and r.realizado):
                continue
            
            sumanry = None
            if accion == "create":
                summary = _('Gestionar viaje para %s del proyecto %s' % (r.employee_id.name, r.task_id.project_id.name))
            elif accion == "update":
                summary = _('Gestionar modificación viaje para %s del proyecto %s' % (r.employee_id.name, r.task_id.project_id.name))
                
            fecha = r.fecha - timedelta(days=5) if r.fecha else None
            
            tasks_activity = None
            if r.pcr:
                tasks_activity = self.env['project.task'].search([
                    ('project_id', '=', r.task_id.project_id.id),
                    ('pcr', '=', True)
                ])
            else:
                tasks_activity = r.task_id
            
            tasks_activity.create_activity(summary, fecha)
    
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
            