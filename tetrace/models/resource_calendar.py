# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

    
class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"
    
    horas = fields.Float('Horas')
    horas_cliente = fields.Float('Horas cliente')
    festivo = fields.Boolean('Festivo')
    festivo_cliente = fields.Boolean('Festivo cliente')
    