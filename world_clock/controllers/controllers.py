# -*- coding: utf-8 -*-
import pytz
from datetime import datetime

from odoo.http import Controller, request, route
import logging
_logger = logging.getLogger(__name__)


class WorldClock(Controller):
    @route('/render_content', type='json', auth="public", website=True)
    def render_content(self, *args, **kw):
        world_clock_obj = request.env['world_clock.world_clock'].sudo().search([('status', '=', True)])
        print('simmi')
        values = {
            'world_clock_obj': [{
                'id': o.id,
                'name': o.name,
                'timezone': o.tz,
                'tzDate': self._get_date(o.tz)
            } for o in world_clock_obj]
        }
        return values

    def _get_date(self, tz):
        if tz:
            format = "%Y-%m-%d %H:%M:%S"
            now_utc = datetime.now(pytz.timezone('UTC'))
            # Convert to Any time zone
            tzd = tz
            if tz[:3] == 'Etc':
                if tz.find('-') != -1:
                    tzd = tz.replace('-', '+')
                elif tz.find('+') != '+':
                    tzd = tz.replace('+', '-')
            now_asia = now_utc.astimezone(pytz.timezone(tzd))
            return now_asia.strftime(format)
