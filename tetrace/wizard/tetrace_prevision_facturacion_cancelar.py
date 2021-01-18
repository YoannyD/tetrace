# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class PrevisionFacturacionCancelar(models.TransientModel):
    _name = 'tetrace.prevision_facturacion_cancelar'
    _description = "Cancelar previsión facturación"
    
    prevision_facturacion_ids = fields.Many2many("tetrace.prevision_facturacion", 
                                               'prevision_facturacion_cancelar_rel', 'gf_id', 'gfc_id')
    feedback = fields.Text("Feedback")
    fecha = fields.Date("Fecha")
    
    def action_cancelar(self):
        self.ensure_one()
        for r in self.prevision_facturacion_ids:
            new_record = r.copy({
                'feedbak': self.feedback,
                'fecha': self.fecha
            })
        self.prevision_facturacion_ids.write({'cancelado': True})

    def open_wizard(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }