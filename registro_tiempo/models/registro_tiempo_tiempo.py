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
    fecha_entrada = fields.Datetime('Fecha entrada')
    fecha_salida = fields.Datetime('Fecha salida')
    unidades_realizadas = fields.Integer("Unidades realizadas")
    observaciones = fields.Text("Observaciones")
    tiempo_parada_ids = fields.One2many("registro_tiempo.tiempo_parada", "tiempo_id")
    horas_trabajadas = fields.Float("Horas trabajadas", compute='_compute_horas_trabajadas', store=True, readonly=True)

    @api.depends("fecha_entrada", "fecha_salida")
    def _compute_horas_trabajadas(self):
        for r in self:
            if r.fecha_entrada and r.fecha_salida:
                delta = r.fecha_salida - r.fecha_entrada
                r.horas_trabajadas = delta.total_seconds() / 3600.0
            else:
                r.horas_trabajadas = False

class RegistroHoraParada(models.Model):
    _name = "registro_tiempo.tiempo_parada"
    _description = "Paradas del registro horas"

    name = fields.Char("Nombre", compute="_compute_name", store=True)
    tipo_parada_id = fields.Many2one("registro_tiempo.tipo_parada", string="Tipo parada", required=True)
    fecha_entrada = fields.Datetime('Fecha entrada')
    fecha_salida = fields.Datetime('Fecha salida')
    tiempo_id = fields.Many2one("registro_tiempo.tiempo", string="Registro hora")
    horas_parada = fields.Float("Horas parada", compute='_compute_horas_parada', store=True, readonly=True)

    @api.depends("tipo_parada_id", "horas_parada")
    def _compute_name(self):
        for r in self:
            r.name = r.tipo_parada_id

    @api.depends("fecha_entrada", "fecha_salida")
    def _compute_horas_parada(self):
        for r in self:
            if r.fecha_entrada and r.fecha_salida:
                delta = r.fecha_salida - r.fecha_entrada
                r.horas_parada = delta.total_seconds() / 3600.0
            else:
                r.horas_parada = False

class TipoParada(models.Model):
    _name = "registro_tiempo.tipo_parada"
    _description = "Tipos de paradas"

    name = fields.Char("Nombre")
    tiempo_parada_ids = fields.One2many("registro_tiempo.tiempo_parada", "tipo_parada_id")

    def get_data_api(self):
        self.ensure_one()
        return {
            "id": self.id,
            "name": self.name
        }
