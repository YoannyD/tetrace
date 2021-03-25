# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

TIPOS = [
    ('parte', _('Parte')),
    ('mob', _('MOB')),
    ('demob', _('DEMOB')),
]


class RegistroTiempo(models.Model):
    _name = "registro_tiempo.tiempo"
    _description = "Registros horas"
    _order = "id desc"

    project_id = fields.Many2one('project.project', string="Proyecto", required=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True)
    tecnico_calendario_id = fields.Many2one('tetrace.tecnico_calendario', string="Técnico calendario",
                                            compute="_compute_tecnico_calendario_id")
    fecha_entrada = fields.Datetime('Fecha entrada')
    dia_semana_fecha_entrada = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Día de la semana', compute="_compute_dia_semana_fecha_entrada", store=True)
    nocturno = fields.Boolean('Nocturno')
    festivo = fields.Boolean('Festivo')
    festivo_cliente = fields.Boolean('Festivo cliente')
    fecha_salida = fields.Datetime('Fecha salida')
    tipo = fields.Selection(TIPOS, string="Tipo")
    unidades_realizadas = fields.Integer("Unidades realizadas")
    observaciones = fields.Text("Observaciones")
    tiempo_parada_ids = fields.One2many("registro_tiempo.tiempo_parada", "tiempo_id")
    horas_trabajadas = fields.Float("Horas trabajadas", compute='_compute_horas_trabajadas', store=True, readonly=True)
    horas_extra = fields.Float('Horas extra')
    horas_extra_cliente = fields.Float('Horas extra cliente')

    @api.depends('fecha_entrada')
    def _compute_dia_semana_fecha_entrada(self):
        for r in self:
            r.dia_semana_fecha_entrada = str(r.fecha_entrada.weekday()) if r.fecha_entrada else False

    @api.depends("fecha_entrada", "fecha_salida")
    def _compute_horas_trabajadas(self):
        for r in self:
            if r.fecha_entrada and r.fecha_salida:
                delta = r.fecha_salida - r.fecha_entrada
                r.horas_trabajadas = delta.total_seconds() / 3600.0
            else:
                r.horas_trabajadas = False

    @api.depends('project_id', 'employee_id')
    def _compute_tecnico_calendario_id(self):
        for r in self:
            tecnico_calendario = self.env['tetrace.tecnico_calendario'].sudo().search([
                ('project_id', '=', r.project_id.id),
                ('employee_id', '=', r.employee_id.id),
            ], limit=1)
            r.tecnico_calendario_id = tecnico_calendario.id

    def es_festivo(self):
        self.ensure_one()
        if self.fecha_entrada and self.tecnico_calendario_id and self.tecnico_calendario_id.es_festivo(self.fecha_entrada):
            return True
        return False

    def es_festivo_cliente(self):
        self.ensure_one()
        if self.fecha_entrada and self.tecnico_calendario_id and self.tecnico_calendario_id.es_festivo_cliente(self.fecha_entrada):
            return True
        return False

    def es_nocturno(self):
        self.ensure_one()
        if self.fecha_entrada:
            hora = int(self.fecha_entrada.strftime('%H'))
            if hora >= 22:
                return True
        return False

    def get_data_api(self):
        self.ensure_one()
        return {'id': self.id,}


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

    def get_data_api(self):
        self.ensure_one()
        return {
            'id': self.id,
        }


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
