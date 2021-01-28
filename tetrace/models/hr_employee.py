# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = "hr.employee"

    codigo_trabajador_A3 = fields.Char('Código A3')
    codigo_drive = fields.Char('Carpeta Drive')
    numero_ss = fields.Char('Nº Seguridad Social')
    IND_NoResidente_A3 = fields.Char('No residente A3')
    sin_adjuntos = fields.Boolean("Sin adjuntos")
    coste_hora = fields.Monetary('Coste hora')
    precio_hora = fields.Monetary('Precio hora')
    document_employee_count = fields.Integer('Documentos', compute="_compute_document_employee")
    contract_clock = fields.Boolean(string='Contract Clock')
    key_nomina = fields.Char('Cláve nómina')
    applicant_ids = fields.One2many('hr.applicant', 'emp_id')
    applicant_count = fields.Integer('Número de procesos de selección', compute="_compute_applicant")
    nivel_validacion_compras_ids = fields.Many2many('tier.definition', string="Validación compras", domain="['&',('model_id','=',586),'|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    alquiler_vehiculo_ids = fields.One2many("tetrace.alquiler_vehiculo", "employee_id")
    alojamiento_ids = fields.One2many("tetrace.alojamiento", "employee_id")
    documentacion_laboral = fields.Char("Documentación laboral")

    def _compute_document_employee(self):
        for r in self:
            documents = self.env['documents.document'].search_count([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', r.id),
            ])
            r.document_employee_count = documents

    def _compute_applicant(self):
        for r in self:
            r.applicant_count = len(r.applicant_ids)
            
    def write(self, vals):
        res = super(Employee, self).write(vals)
        self.actualizar_nombre_adjunto_a_documento()
        return res
    
    def actualizar_nombre_adjunto_a_documento(self):
        for r in self:
            documents = self.env['documents.document'].search([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', r.id)
            ])
            documents._compute_res_name()
            
    def action_task_employee_view(self):
        self.ensure_one()
        tasks = self.env['project.task'].search([
            ('employee_id', '=', self.id),
            ('tarea_individual', '=', True)
        ])
        project_ids = [task.project_id.id for task in tasks]
        action = self.env['ir.actions.act_window'].for_xml_id('project', 'open_view_project_all')
        action.update({'domain': [('id', 'in', project_ids)]})
        return action
