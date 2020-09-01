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
    contract_clock = fields.Boolean(string='Contract Warning')
    key_nomina = fields.Char('Cláve nómina')

    def _compute_document_employee(self):
        for r in self:
            documents = self.env['documents.document'].search_count([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', r.id),
            ])
            r.document_employee_count = documents
