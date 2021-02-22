# -*- coding: utf-8 -*-
# © 20021 Ingetive - <info@ingetive.com>

import pytz
import logging

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields

_logger = logging.getLogger(__name__)

def timezone(self):
    return pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Europe/Madrid')

def time_float_to_str(hora):
    return '{0:02.0f}:{1:02.0f}:00'.format(*divmod(hora * 60, 60))

def time_str_to_float(hora_str):
    _logger.warning(hora_str)
    hora = hora_str.split(":")
    a =  float(hora[0]) + (float(hora[1]) / 60)
    _logger.warning(a)
    return a

def date_str_to_float_time(fecha):
    _logger.warning(fecha.split(" ")[1])
    return time_str_to_float(fecha.split(" ")[1])
