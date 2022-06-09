# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta

_logger = logging.getLogger(__name__)


class imputacionhoras(models.Model):
    _name = "tetrace.imputacion_proyectos"
    _description = "Imputación Proyectos"
    
    project_id = fields.Many2one('project.project', 'Project')
    concepto_id = fields.Many2one('tetrace.imputacion_proyecto_nombre', string="Concepto")
    unidades = fields.Integer(string="Unidades")
    precio = fields.Integer(string="importe")
    total = fields.Integer(string="total",compute="_compute_total_linea")
    
    @api.depends('unidades','precio')
    def _compute_total_linea(self):
        for r in self:
            r.total = r.precio * r.unidades

    
class imputacionhorasnombre(models.Model):
    _name = "tetrace.imputacion_proyecto_nombre"
    _description = "Nombre imputación proyectos"
    
    
    name = fields.Char(string="Nombre")
    
    _sql_constraints = [
        ("name_uniq", "unique(name)", _("El nombre ya esta en la lista"),)
    ]