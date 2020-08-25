# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from datetime import datetime, timedelta

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
    contract_clock = fields.Boolean(string='Contract Warning', store=True, compute='_compute_contract_clock',
                                    groups="hr.group_hr_user")

    def _compute_document_employee(self):
        for r in self:
            documents = self.env['documents.document'].search_count([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', r.id),
            ])
            r.document_employee_count = documents

    @api.depends('contract_id', 'contract_id.date_end', 'contract_id.trial_date_end')
    def _compute_contract_clock(self):
        fecha_fin_contrato = fields.Date.today() + timedelta(days=15)
        fecha_fin_prueba = fields.Date.today() + timedelta(days=7)
        for r in self:
            clock = False
            if r.contract_id and (r.contract_id.date_end != False and r.contract_id.date_end <= fecha_fin_contrato) or \
                (r.contract_id.trial_date_end != False and r.contract_id.trial_date_end <= fecha_fin_prueba):
                clock = True
            r.contract_clock = clock
