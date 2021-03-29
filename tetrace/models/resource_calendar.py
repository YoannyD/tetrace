# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    country_id = fields.Many2one('res.country', string="País")

    def cargar_festivos(self):
        for r in self:
            if r.country_id:
                festivos = self.env['tetrace.festivo'].search([('country_id', '=', r.country_id.id)])
                Leaves = self.env['resource.calendar.leaves']
                for festivo in festivos:
                    leave = Leaves.search([
                        ('calendar_id', '=', r.id),
                        ('date_from', '=', festivo.fecha_inicio.strftime("%Y-%m-%d 00:00:00")),
                        ('date_to', '=', festivo.fecha_fin.strftime("%Y-%m-%d 00:00:00")),
                    ], limit=1)

                    if leave:
                        leave.write({'name': festivo.name})
                    else:
                        Leaves.create({
                            'name': festivo.name,
                            'date_from': festivo.fecha_inicio.strftime("%Y-%m-%d 00:00:00"),
                            'date_to': festivo.fecha_fin.strftime("%Y-%m-%d 00:00:00"),
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
