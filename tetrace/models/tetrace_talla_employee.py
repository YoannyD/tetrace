# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import timedelta

_logger = logging.getLogger(__name__)


class TallaEmployee(models.Model):
    _name = "tetrace.talla_employee"
    _description = "Tallas Empleados"
    
    
    emp_id = fields.Many2one("hr.employee", string="Empleado")
    concepto_id = fields.Many2one('tetrace.talla_concepto', string="Concepto")
    talla = fields.Char(string="Talla")

    
class TallaConcepto(models.Model):
    _name = "tetrace.talla_concepto"
    _description = "Conceptos Tallas"
    
    
    name = fields.Char(string="Nombre")