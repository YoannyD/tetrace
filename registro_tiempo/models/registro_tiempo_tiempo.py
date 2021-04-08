# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging
import pytz

from odoo import models, fields, api, _
from odoo.addons.registro_tiempo.models.date_utils import union_date_time_tz, time_float_to_str
from odoo.exceptions import ValidationError

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
                                            compute="_compute_tecnico_calendario")
    resource_calendar_id = fields.Many2one("resource.calendar", string="Calendario laboral",
                                            compute="_compute_tecnico_calendario")
    fecha_entrada = fields.Date('Fecha entrada')
    hora_entrada = fields.Float('Hora entrada', default=0.0)
    fecha_hora_entrada = fields.Datetime('Fecha/Hora entrada', compute="_compute_fecha_hora_entrada", store=True)
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
    fecha_salida = fields.Date('Fecha salida')
    hora_salida = fields.Float('Hora salida', default=0.0)
    fecha_hora_salida = fields.Datetime('Fecha/Hora salida', compute="_compute_fecha_hora_salida", store=True)
    tipo = fields.Selection(TIPOS, string="Tipo")
    unidades_realizadas = fields.Integer("Unidades realizadas")
    observaciones = fields.Text("Observaciones")
    tiempo_parada_ids = fields.One2many("registro_tiempo.tiempo_parada", "tiempo_id")
    horas_trabajadas = fields.Float("Horas trabajadas", compute='_compute_horas_trabajadas', store=True, readonly=True)
    horas_extra = fields.Float('Horas extras')
    horas_extra_cliente = fields.Float('Horas extras cliente')

    @api.constrains("fecha_hora_entrada", "fecha_hora_salida")
    def _check_fechas_hora(self):
        for r in self:
            if r.fecha_hora_entrada and r.fecha_hora_salida and r.fecha_hora_entrada > r.fecha_hora_salida:
                raise ValidationError(_("La fecha de salida tiene que se superior a la de entrada"))

    @api.depends('fecha_entrada', 'hora_entrada')
    def _compute_fecha_hora_entrada(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        for r in self:
            fecha = None
            if r.fecha_entrada:
                fecha = union_date_time_tz(r.fecha_entrada, r.hora_entrada, user_tz)
                fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")

            r.fecha_hora_entrada = fecha

    @api.depends('fecha_entrada')
    def _compute_dia_semana_fecha_entrada(self):
        for r in self:
            r.dia_semana_fecha_entrada = str(r.fecha_entrada.weekday()) if r.fecha_entrada else False

    @api.depends("fecha_hora_entrada", "fecha_hora_salida")
    def _compute_horas_trabajadas(self):
        for r in self:
            horas = 0
            if r.fecha_hora_entrada and r.fecha_hora_salida:
                delta = r.fecha_hora_salida - r.fecha_hora_entrada
                horas = delta.total_seconds() / 3600.0
                if horas < 0:
                    horas = 0
            r.horas_trabajadas = horas

    @api.depends('fecha_salida', 'hora_salida')
    def _compute_fecha_hora_salida(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        for r in self:
            fecha = None
            if r.fecha_salida:
                fecha = union_date_time_tz(r.fecha_salida, r.hora_salida, user_tz)
                fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")
            r.fecha_hora_salida = fecha

    @api.depends('project_id', 'employee_id')
    def _compute_tecnico_calendario(self):
        for r in self:
            tecnico_calendario = self.env['tetrace.tecnico_calendario'].sudo().search([
                ('project_id', '=', r.project_id.id),
                ('employee_id', '=', r.employee_id.id),
            ], limit=1)
            r.update({
                'tecnico_calendario_id': tecnico_calendario.id,
                'resource_calendar_id': tecnico_calendario.resource_calendar_id.id if tecnico_calendario.resource_calendar_id else False
            })

    def es_festivo(self):
        self.ensure_one()
        if self.fecha_entrada and self.resource_calendar_id and \
            self.resource_calendar_id.es_festivo(self.fecha_entrada):
            return True
        return False

    def es_festivo_cliente(self):
        self.ensure_one()
        if self.fecha_entrada and self.resource_calendar_id and \
            self.resource_calendar_id.es_festivo_cliente(self.fecha_entrada):
            return True
        return False

    def es_nocturno(self):
        self.ensure_one()
        return True if self.hora_entrada < 6 or self.hora_entrada >= 22 else False

    def get_horas_extra(self):
        self.ensure_one()
        if self.horas_trabajadas and self.resource_calendar_id:
            attendance = self.resource_calendar_id.get_attendance(self.fecha_entrada)
            if attendance:
                horas_extra = self.horas_trabajadas - attendance.horas
                return horas_extra if horas_extra >= 0 else 0
        return 0

    def get_horas_extra_cliente(self):
        self.ensure_one()
        if self.horas_trabajadas and self.resource_calendar_id:
            attendance = self.resource_calendar_id.get_attendance(self.fecha_entrada)
            if attendance:
                horas_extra = self.horas_trabajadas - attendance.horas_cliente
                return horas_extra if horas_extra >= 0 else 0
        return 0

    def get_data_api(self):
        self.ensure_one()
        tipo = ""
        if self.tipo:
            tipo = dict(self._fields['tipo'].selection).get(self.tipo)

        dia_semana_fecha_entrada = ""
        if self.dia_semana_fecha_entrada:
            dia_semana_fecha_entrada = dict(self._fields['dia_semana_fecha_entrada'].selection).get(self.dia_semana_fecha_entrada)

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        fecha_hora_entrada = ""
        if self.fecha_hora_entrada:
            fecha_hora_entrada = self.fecha_hora_entrada\
                .astimezone(user_tz)\
                .replace(tzinfo=None)\
                .strftime("%Y/%m/%d %H:%M:00")

        fecha_hora_salida = ""
        if self.fecha_hora_salida:
            fecha_hora_salida = self.fecha_hora_salida \
                .astimezone(user_tz) \
                .replace(tzinfo=None) \
                .strftime("%Y/%m/%d %H:%M:00")

        data = {
            'id': self.id,
            'project_id': self.project_id.id or 0,
            'project_name': self.project_name or "",
            'tipo': tipo,
            'festivo': self.festivo or False,
            'nocturno': self.nocturno or False,
            'fecha_hora_entrada': fecha_hora_entrada,
            'fecha_hora_salida': fecha_hora_salida,
            'dia_semana_fecha_entrada': dia_semana_fecha_entrada,
            'horas_trabajadas': self.horas_trabajadas or 0,
            'horas_extra': self.horas_extra or 0,
            'horas_extra_cliente': self.horas_extra_cliente or 0,
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
