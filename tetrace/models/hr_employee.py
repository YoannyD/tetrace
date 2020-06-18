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
