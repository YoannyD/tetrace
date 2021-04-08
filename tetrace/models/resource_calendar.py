# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging
import pytz

from odoo import models, fields, api, _
from datetime import datetime, date

_logger = logging.getLogger(__name__)

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    country_id = fields.Many2one('res.country', string="País")

    def es_festivo_global(self, fecha):
        self.ensure_one()
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')

        if type(fecha) is date:
            fecha_aux = user_tz.localize(fields.Datetime.from_string('%s %s' % (fecha, '00:00:00'))).astimezone(pytz.timezone('UTC'))
            fecha_str = fecha_aux.strftime("%Y-%m-%d %H:%M:%S")
        elif type(fecha) is datetime:
            fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return False

        leave = self.env['resource.calendar.leaves'].sudo().search([
            ('calendar_id', '=', self.id),
            ('date_from', '<=', fecha_str),
            ('date_to', '>=', fecha_str),
        ], limit=1)

        if leave:
            return True
        return False

    def es_festivo(self, fecha):
        self.ensure_one()
        if self.es_festivo_global(fecha):
            return True

        festivo = True
        for attendance in self.attendance_ids:
            if attendance.dayofweek == str(fecha.weekday()):
                if attendance.festivo:
                    return True
                else:
                    festivo = False

        return festivo

    def es_festivo_cliente(self, fecha):
        self.ensure_one()
        if self.es_festivo_global(fecha):
            return True

        festivo = True
        for attendance in self.attendance_ids:
            if attendance.dayofweek == str(fecha.weekday()):
                if attendance.festivo_cliente:
                    return True
                else:
                    festivo = False

        return festivo

    def get_attendance(self, fecha):
        self.ensure_one()
        for attendance in self.attendance_ids:
            if attendance.dayofweek == str(fecha.weekday()):
                return attendance
        return None

    def cargar_festivos(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        for r in self:
            if r.country_id:
                festivos = self.env['tetrace.festivo'].search([('country_id', '=', r.country_id.id)])
                Leaves = self.env['resource.calendar.leaves']
                for festivo in festivos:
                    fecha_inicio = user_tz.localize(fields.Datetime.from_string('%s %s' % (festivo.fecha_inicio, '00:00:00'))).astimezone(pytz.timezone('UTC'))
                    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d %H:%M:%S")
                    fecha_fin = user_tz.localize(fields.Datetime.from_string('%s %s' % (festivo.fecha_inicio, '23:59:59'))).astimezone(pytz.timezone('UTC'))
                    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d %H:%M:%S")

                    leave = Leaves.search([
                        ('calendar_id', '=', r.id),
                        ('date_from', '=', fecha_inicio_str),
                        ('date_to', '=', fecha_fin_str),
                    ], limit=1)

                    if leave:
                        leave.write({'name': festivo.name})
                    else:
                        Leaves.create({
                            'name': festivo.name,
                            'date_from': fecha_inicio_str,
                            'date_to': fecha_fin_str,
                            'calendar_id': r.id
                        })


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    name = fields.Char(default=lambda self: _('New'), copy=False)
    date_from = fields.Date(default=lambda self: fields.Date.today())
    date_to = fields.Date(default=lambda self: fields.Date.today())
    horas = fields.Float('Horas')
    horas_cliente = fields.Float('Horas cliente')
    festivo = fields.Boolean('Festivo')
    festivo_cliente = fields.Boolean('Festivo cliente')

    @api.model
    def create(self, vals):
        res =  super(ResourceCalendarAttendance, self).create(vals)
        if res.name == _('New'):
            res.write({'name': dict(res._fields['dayofweek'].selection).get(res.dayofweek)})
        return res
