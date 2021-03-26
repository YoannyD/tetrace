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
    project_name = fields.Char(related="project_id.name", store="True")
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True)
    tecnico_calendario_id = fields.Many2one('tetrace.tecnico_calendario', string="Técnico calendario",
                                            compute="_compute_tecnico_calendario_id")
    fecha_entrada = fields.Datetime('Fecha entrada')
    dia_semana_fecha_entrada = fields.Selection([
        ('0', _('Monday')),
        ('1', _('Tuesday')),
        ('2', _('Wednesday')),
        ('3', _('Thursday')),
        ('4', _('Friday')),
        ('5', _('Saturday')),
        ('6', _('Sunday'))
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
        tipo = ""
        if self.tipo:
            tipo = dict(self._fields['tipo'].selection).get(self.tipo)

        dia_semana_fecha_entrada = ""
        if self.dia_semana_fecha_entrada:
            dia_semana_fecha_entrada = dict(self._fields['dia_semana_fecha_entrada'].selection).get(
                self.dia_semana_fecha_entrada)

        data = {
            'id': self.id,
            'project_id': self.project_id.id or 0,
            'project_name': self.project_name or "",
            'tipo': tipo,
            'festivo': self.festivo,
            'nocturno': self.nocturno,
            'fecha_entrada': self.fecha_entrada.strftime("%d/%m/%Y %H:%m") if self.fecha_entrada else "",
            'fecha_salida': self.fecha_salida.strftime("%d/%m/%Y %H:%m") if self.fecha_salida else "",
            'dia_semana_fecha_entrada': dia_semana_fecha_entrada,
            'horas_trabajadas': self.horas_trabajadas or "",
            'horas_extra': self.horas_extra or "",
        }
        return data


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
        return {'id': self.id,}


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
