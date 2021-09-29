# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Applicant(models.Model):
    _inherit = "helpdesk.ticket"
    
 
    enlace = fields.Text("Enlace incidencia",copy=False)
    bloqueado = fields.Boolean("Bloqueado",copy=False)
    confirmado = fields.Boolean("Confirmado por usuario",copy=False)
    fecha_limite = fields.Datetime(string="Fecha limite",copy=False)
    
    
