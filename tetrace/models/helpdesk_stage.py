# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HelpdeskStage(models.Model):
    _inherit = "helpdesk.stage"
    
    validado = fields.Boolean("Validado")
    resuelto = fields.Boolean("Resuelto")
    es_reabrir = fields.Boolean("Etapa de reabrir")