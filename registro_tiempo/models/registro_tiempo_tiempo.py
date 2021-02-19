# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class RegistroTiempo(models.Model):
    _name = "registro_tiempo.tiempo"
    _description = "Registros horas"

    project_id = fields.Many2one('project.project', string="Proyecto")
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    fecha = fields.Date('Fecha')
    hora_inicio = fields.Float('Hora inicio')
    hora_fin = fields.Float('Hora fin')
    unidades_realizadas = fields.Integer("Unidades realizadas")
    observaciones = fields.Text("Observaciones")
    tiempo_parada_ids = fields.One2many("registro_tiempo.tiempo_parada", "tiempo_id")


class RegistroHoraParada(models.Model):
    _name = "registro_tiempo.tiempo_parada"
    _description = "Paradas del registro horas"

    name = fields.Char('Tipo paradas')
    hora_inicio = fields.Float('Hora inicio')
    hora_fin = fields.Float('Hora fin')
    tiempo_id = fields.Many2one("registro_tiempo.tiempo", string="Registro hora")
