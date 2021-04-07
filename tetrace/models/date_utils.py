# -*- coding: utf-8 -*-
# © 20021 Ingetive - <info@ingetive.com>

import pytz
import logging
import math
from odoo.tools.float_utils import float_round

from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from odoo import fields

_logger = logging.getLogger(__name__)

def timezone(self):
    return pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Europe/Madrid')

def sum_time_for_date(fecha, hora):
    tiempo = '{0:02.0f}:{1:02.0f}:00'.format(*divmod(hora * 60, 60)).split(":")
    return fecha + timedelta(hours=float(tiempo[0]), minutes=float(tiempo[1]))

def union_date_time(fecha, hora):
    fecha_str = fecha.strftime("%Y-%m-%d")
    hora_str = time_float_to_str(hora)
    return fields.Datetime.from_string('%s %s' % (fecha_str, hora_str))

def union_date_time_tz(fecha, hora, tz):
    fecha_str = fecha.strftime("%Y-%m-%d")
    hora_str = time_float_to_str(hora)
    return tz.localize(fields.Datetime.from_string('%s %s' % (fecha_str, hora_str))).astimezone(pytz.timezone('UTC'))

def time_float_to_str(hora):
    return '{0:02.0f}:{1:02.0f}:00'.format(*divmod(hora * 60, 60))

def time_str_to_float(hora_str):
    hora = hora_str.split(":")
    a =  float(hora[0]) + (float(hora[1]) / 60)
    return a

def date_str_to_float_time(fecha):
    return time_str_to_float(fecha.split(" ")[1])

def float_to_time(hours):
    if hours == 24.0:
        return time.max
    fractional, integral = math.modf(hours)
    return time(int(integral), int(float_round(60 * fractional, precision_digits=0)), 0)

def date_from_string(fecha):
    try:
        fecha = fields.Date.from_string(fecha)
    except:
        fecha = False
    return fecha

def datetime_from_string(fecha):
    try:
        fecha = fields.Datetime.from_string(fecha)
    except:
        fecha = False
    return fecha
