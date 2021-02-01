# -*- coding: utf-8 -*-
import random
import pytz
from datetime import datetime

from dateutil import rrule
from dateutil.relativedelta import relativedelta
from babel.dates import format_datetime

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

# put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]


def _tz_get(self):
    return _tzs


class WorldClock(models.Model):
    _name = 'world_clock.world_clock'
    _description = 'WorldClock clock'

    name = fields.Char(required=True)
    tz = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'),
                          help="When printing documents and exporting/importing data, time values are computed according to this timezone.\n"
                               "If the timezone is not set, UTC (Coordinated Universal Time) is used.\n"
                               "Anywhere else, time values are computed according to the time offset of your web client.")
    tzDate = fields.Datetime(string="Date", store=False, compute='_get_date', required=True)
    status = fields.Boolean(default=True)
    color = fields.Integer()

    @api.depends('tz')
    def _get_date(self):
        for r in self:
            if r.tz:
                format = "%Y-%m-%d %H:%M:%S"
                now_utc = datetime.now(pytz.timezone('UTC'))
                # Convert to Any time zone
                tz = r.tz
                if r.tz[:3] == 'Etc':
                    if r.tz.find('-') != -1:
                        tz = r.tz.replace('-', '+')
                    elif r.tz.find('+') != '+':
                        tz = r.tz.replace('+', '-')
                now_asia = now_utc.astimezone(pytz.timezone(tz))
                r.tzDate = now_asia.strftime(format)

