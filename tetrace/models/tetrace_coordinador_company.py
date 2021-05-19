# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CoordinadorCompany(models.Model):
    _name = "tetrace.coordinador_company"
    _description = "Coordinadores (Compañia)"
    
    tipo_proyecto_id = fields.Many2one('tetrace.tipo_proyecto', string="Tipo de proyecto")
    company_id = fields.Many2one('res.company', string="Compañia")
    coordinador_id = fields.Many2one('res.users', string="Coordinador")
    seguidor_ids = fields.Many2many('res.users')