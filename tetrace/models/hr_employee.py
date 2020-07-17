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
    # documento_url = fields.Char('Documento', compute="_compute_documento_url")
    #
    # def _compute_documento_url(self):
    #     menu_id = self.env.ref('documents.menu_root').id
    #     action_id = self.env.ref('documents.document_action').id
    #     for r in self:
    #         r.url_form = "/web#model=documents.document&view_type=kanban&menu_id=%s&action=%s" % (menu_id, action_id)
    #
    def action_view_documentos(self):
        return {
            'name': 'Documentos',
            'type': 'ir.actions.act_window',
            'res_model': 'documents.document',
            'view_mode': 'kanban,tree,form',
            'view_ids': [(5, 0, 0),
                    (0, 0, {'view_mode': 'kanban', 'view_id': self.env.ref('documents.document_view_kanban')}),
                    (0, 0, {'view_mode': 'tree', 'view_id': False}),
                    (0, 0, {'view_mode': 'form', 'view_id': self.env.ref('documents.document_view_form')})],
            'target': "inline"
        }
