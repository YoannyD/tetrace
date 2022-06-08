# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Formacion(models.Model):
    _name = "tetrace.formacion"
    _description = "Formaciones"
    
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True)
    fecha_inicio = fields.Date('Fecha inicio', required="True")
    fecha_fin = fields.Date('Fecha fin', required="True")
    tipo_id = fields.Many2one("tetrace.tipo_formacion", string="Tipo", required="True")
    curso = fields.Char('Curso', required="True")
    fecha_vigencia = fields.Date('Vigencia', required="True")
    certificado = fields.Char('Certificado')
    

class TipoFormacion(models.Model):
    _name = "tetrace.tipo_formacion"
    _description = "Tipos Formación"
    
    name = fields.Char("Nombre", required=True)
    formacion_ids = fields.One2many("tetrace.formacion", "tipo_id")
    
    _sql_constraints = [
        ("name_uniq", "unique(name)", _("El nombre tiene que ser único"),)
    ]
    