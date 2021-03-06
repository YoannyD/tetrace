# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Applicant(models.Model):
    _inherit = "hr.applicant"

    country_id = fields.Many2one('res.country', string="País")
    job_ids = fields.Many2many('hr.job', 'applicant_id', string="Otro puesto de trabajo")
    carpeta_drive = fields.Char('Carpeta Drive')
    fecha_recepcion = fields.Date('Fecha recepción')
    sin_adjuntos = fields.Boolean('Sin adjuntos en Drive')
    categ_ids = fields.Many2many(string='Formación')
    priority = fields.Selection(selection_add=[('4', 'Perfecto')], default='2')
    icono_warning = fields.Boolean('Alerta')
    referencia = fields.Char('Referencia Tetrace')
    resume_line_ids = fields.One2many('tetrace.resume.line', 'applicant_id', string="Resumé lines")
    applicant_skill_ids = fields.One2many('tetrace.applicant.skill', 'applicant_id', string="Habilidades")
    document_applicant_count = fields.Integer('Documentos', compute="_compute_document_applicant")
    proceso_seleccion_id = fields.Many2one('tetrace.proceso_seleccion', string="Proceso de selección")
    project_ids = fields.Many2many('project.project')
    reference = fields.Char("Reference")
    habilidad_ids = fields.Many2many('tetrace.habilidad_applicant')
    observaciones = fields.Text("Observaciones")
    feedback_ids = fields.One2many("tetrace.feedback_applicant", "applicant_id")
    competencia = fields.Boolean('Competencia')
    empresa_competencia = fields.Text("Empresa de la competencia")
    

    @api.model
    def create(self, vals):
        res = super(Applicant, self).create(vals)
        res.reference = "P" + str(res.id + 1)
        return res

        
    def _compute_document_applicant(self):
        for r in self:
            docs_applicant = self.env['documents.document'].search_count([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', r.id),
            ])
            
            docs_employee = self.env['documents.document'].search_count([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', r.emp_id.id),
            ])
            
            r.document_applicant_count = docs_applicant + docs_employee
    
    def write(self, vals):
        res = super(Applicant, self).write(vals)
        self.actualizar_nombre_adjunto_a_documento()
        return res
    
    def actualizar_nombre_adjunto_a_documento(self):
        for r in self:
            documents = self.env['documents.document'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', r.id)
            ])
            documents._compute_res_name()
    
    def create_employee_from_applicant(self):
        res = super(Applicant, self).create_employee_from_applicant()
        
        for applicant in self:
            if applicant.emp_id and applicant.emp_id.id == res['res_id']:
                values = {}
                for line in applicant.resume_line_ids:
                    if 'resume_line_ids' not in values:
                        values.update({'resume_line_ids': []})
                        
                    values['resume_line_ids'].append((0, 0, {
                        'name': line.name,
                        'date_start': line.date_start,
                        'date_end': line.date_end,
                        'description': line.description,
                        'line_type_id': line.line_type_id.id if line.line_type_id else None,
                        'display_type': line.display_type,
                    }))
                    
                for skill in applicant.applicant_skill_ids:
                    if 'employee_skill_ids' not in values:
                        values.update({'employee_skill_ids': []})
                        
                    values['employee_skill_ids'].append((0, 0, {
                        'skill_id': skill.skill_id.id if skill.skill_id else None,
                        'skill_level_id': skill.skill_level_id.id if skill.skill_level_id else None,
                        'skill_type_id': skill.skill_type_id.id if skill.skill_type_id else None,
                    }))
                if 'resume_line_ids' in values:
                    applicant.emp_id.resume_line_ids.unlink()
                applicant.emp_id.write(values)
                applicant.traspasar_adjuntos_a_empleado()
        return res
    
    def traspasar_adjuntos_a_empleado(self):
        for r in self:
            if not r.emp_id:
                continue
                
            documents = self.env['documents.document'].search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', r.id),
            ])
            for document in documents:
                values = {
                    'res_model': 'hr.employee',
                    'res_id': r.emp_id.id,
                    'datas': document.datas
                }
                
                folder_id = None
                if document.folder_id.id not in [10, 8, 9, 7, 4]:
                    folder_id = 4
                    if document.folder_id.id == 11: #Datos laborables
                        folder_id = 10 
                    elif document.folder_id.id == 12: #Datos formacion
                        folder_id = 8 
                    elif document.folder_id.id == 13: #PRL
                        folder_id = 9
                    elif document.folder_id.id == 14: #Datos personales
                        folder_id = 7
                    elif document.name == 'CV_%s' % r.emp_id.name:
                        folder_id = 7 #carpeta Datos personales
                    elif document.name in ['PROPUESTA LABORAL_V1_%s' % r.emp_id.name, 
                                           'PROPUESTA LABORAL_V2_%s' % r.emp_id.name]:
                        folder_id = 10 #carpeta Datos laborales
                    
                if folder_id:
                    values.update({'folder_id': folder_id})
                document.write(values)
    
    def view_documentos(self):
        action = self.env['ir.actions.act_window'].for_xml_id('documents', 'document_action')
        document_ids = []
        documents = self.env['documents.document'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', self.id),
        ])
        document_ids += documents.ids
        
        if self.emp_id:
            documents = self.env['documents.document'].search([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', self.emp_id.id),
            ])
            document_ids += documents.ids
        
        action.update({'domain': [('id', 'in', document_ids)]})
        return action
    

class ApplicationResumeLine(models.Model):
    _name = 'tetrace.resume.line'
    _description = "Currículums vitaes"
    _order = "line_type_id, date_end desc, date_start desc"

    applicant_id = fields.Many2one('hr.applicant', required=True, ondelete='cascade')
    name = fields.Char("Nombre", required=True, translate=True)
    date_start = fields.Date("Fecha inicio", required=True)
    date_end = fields.Date("Fecha fin")
    description = fields.Text("Description", translate=True)
    line_type_id = fields.Many2one('hr.resume.line.type', string="Tipo")
    display_type = fields.Selection([('classic', 'Classic')], string="Display Type", default='classic')
    date_actual = fields.Boolean('Actual')
    _sql_constraints = [
        ('date_check', "CHECK ((date_start <= date_end OR date_end = NULL))", _("The start date must be anterior to the end date.")),
    ]

    
class HabilidadApplicant(models.Model):
    _name = "tetrace.habilidad_applicant"
    _description = "Habilidades proceso de selección"
    
    name = fields.Char("name", required=True, index=True)
    applicant_ids = fields.Many2many("hr.applicant")
    
    _sql_constraints = [
        ("name_unique", "unique(name)", "El nombre",)
    ]
    

class FeedbackApplicant(models.Model):
    _name = "tetrace.feedback_applicant"
    _description = "Feedback proceso de selección"
    _rec_name = "origen"
    
    fecha = fields.Date("Fecha")
    origen = fields.Char("Origen")
    user_id = fields.Many2one("res.users", string="Usuario")
    comentarios = fields.Text("Comentarios")
    applicant_id = fields.Many2one('hr.applicant', string="Proceso de selección")