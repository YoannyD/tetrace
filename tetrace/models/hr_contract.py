# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Contract(models.Model):
    _inherit = "hr.contract"

    tipo_contrato_id = fields.Many2one('tetrace.tipo_contrato', string="Tipo de contrato")
    percentage = fields.Char(string="Porcentaje Jornada")
    
    def write(self, vals):
        res = super(Contract, self).write(vals)
        self.actualizar_nombre_adjunto_a_documento()
        return res
    
    def actualizar_nombre_adjunto_a_documento(self):
        for r in self:
            documents = self.env['documents.document'].search([
                ('res_model', '=', 'hr.contract'),
                ('res_id', '=', r.id)
            ])
            documents._compute_res_name()
