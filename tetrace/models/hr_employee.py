# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = "hr.employee"

    codigo_trabajador_A3 = fields.Char('Código Externo')
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
    nivel_validacion_compras_ids = fields.Many2many('tier.definition', string="Validación compras", check_company=True, 
                                                    domain="['&',('model_id','=',586),'|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    alquiler_vehiculo_ids = fields.One2many("tetrace.alquiler_vehiculo", "employee_id")
    alojamiento_ids = fields.One2many("tetrace.alojamiento", "employee_id")
    documentacion_laboral = fields.Char("Documentación laboral")
    formacion_ids = fields.One2many('tetrace.formacion', 'employee_id')
    tecnico_calendario_ids = fields.One2many('tetrace.tecnico_calendario', 'employee_id')
    country_visado_id = fields.Many2one('res.country', string="País Visado")
    type_visado_id = fields.Many2one('hr.visado', string="Tipo de Visado")
    reference_employee = fields.Char(compute="_compute_reference", string="Código")
    project_asignado_id = fields.Many2one('project.project', string="Proyecto asignado",
                                          compute="_compute_project_asginado")
    project_country_asignado_id = fields.Many2one('res.country', string="País del proyecto asignado",
                                                 compute="_compute_project_asginado")
  
    def _compute_reference(self):
        self.reference_employee = "E" + str(self.id + 1)
    
    def _compute_project_asginado(self):
        for r in self:
            tecnico_calendario = self.env['tetrace.tecnico_calendario'].search([
                ('employee_id', '=', r.id),
                ('fecha_inicio', '<=', fields.Date.today()),
                '|',
                ('fecha_fin', '=', None),
                ('fecha_fin', '>=', fields.Date.today()),
            ], limit=1)
            project_id = None
            country_id = None
            if tecnico_calendario:
                project_id = tecnico_calendario.project_id.id
                country_id = tecnico_calendario.project_id.company_id.country_id.id
            
            r.update({
                'project_asignado_id': project_id,
                'project_country_asignado_id': country_id
            })
    
    def _compute_document_employee(self):
        for r in self:
            docs_applicant = self.env['documents.document'].search_count([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', 'in', [a.id for a in self.applicant_ids]),
            ])
            
            docs_employee = self.env['documents.document'].search_count([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', r.id),
            ])
            
            r.document_employee_count = docs_applicant + docs_employee

    def _compute_applicant(self):
        for r in self:
            r.applicant_count = len(r.applicant_ids)
        
    @api.onchange('job_id')
    def _onchange_job_id(self):
        super(Employee, self)._onchange_job_id()
        if self.job_id:
            self.department_id = self.job_id.department_id.id
        
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
            
    def view_documentos(self):
        action = self.env['ir.actions.act_window'].for_xml_id('documents', 'document_action')
        document_ids = []
        if self.applicant_ids:
            documents = self.env['documents.document'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', 'in', [a.id for a in self.applicant_ids]),
            ])
            document_ids += documents.ids
        
        documents = self.env['documents.document'].search([
            ('res_model', '=', 'hr.employee'),
            ('res_id', '=', self.emp_id.id),
        ])
        document_ids += documents.ids
        
        action.update({'domain': [('id', 'in', document_ids)]})
        return action

class HrVisado(models.Model):
    _name = "hr.visado"
    _description = "Tipo Visado"
    name = fields.Char(string="Tipo")
