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

    def action_view_documentos(self):
        action = self.env.ref('documents.document_action').read()[0]
        action['domain'] = [('res_model', '=', 'hr.employee'), ('res_id', '=', self.id)]
        return action
