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

    # def _compute_documento_url(self):
    #     menu_id = self.env.ref('crm.crm_menu_root').id
    #     action_id = self.env.ref('crm.action_your_pipeline').id
    #     for r in self:
    #         r.url_form = "/web#id=%s&model=crm.lead&view_type=form&menu_id=%s&action=%s" % (r.id, menu_id, action_id)

    def action_view_documentos(self):
        action = self.env.ref("documents.document_action")
        action.update({
            'context': {
                'default_res_model': 'hr.employee',
                'res_id': self.id
            }
        })
        return action
