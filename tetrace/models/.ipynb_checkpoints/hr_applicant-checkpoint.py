# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

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

    def _compute_document_applicant(self):
        for r in self:
            documents = self.env['documents.document'].search_count([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', r.id),
            ])
            r.document_applicant_count = documents
            
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
                folder_id = False
                if document.name == 'CV_%s' % r.emp_id.name:
                    folder_id = 7 #carpeta Datos personales
                elif document.name in ['PROPUESTA LABORAL_V1_%s' % r.emp_id.name, 
                                       'PROPUESTA LABORAL_V2_%s' % r.emp_id.name]:
                    folder_id = 10 #carpeta Datos laborales
                    
                if folder_id:
                    document.copy({
                        'res_model': 'hr.employee',
                        'res_id': r.emp_id.id,
                        'folder_id': folder_id,
                        'datas': document.datas
                    })


class ApplicationResumeLine(models.Model):
    _name = 'tetrace.resume.line'
    _description = "Currículums vitaes"
    _order = "line_type_id, date_end desc, date_start desc"

    applicant_id = fields.Many2one('hr.applicant', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date()
    description = fields.Text(string="Description")
    line_type_id = fields.Many2one('hr.resume.line.type', string="Tipo")
    display_type = fields.Selection([('classic', 'Classic')], string="Display Type", default='classic')

    _sql_constraints = [
        ('date_check', "CHECK ((date_start <= date_end OR date_end = NULL))", "The start date must be anterior to the end date."),
    ]