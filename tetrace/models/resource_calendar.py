# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


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
