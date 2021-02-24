# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class Attendance(models.Model):
    _inherit = 'hr.attendance'

    latitude_entrada = fields.Float('Latitud entrada', digits=(16, 5))
    longitude_entrada = fields.Float('Longitud entrada', digits=(16, 5))
    ubicacion_maps_entrada = fields.Char("Ubicación marcaje entrada", compute="_compute_ubicacion_maps_entrada")
    latitude_salida = fields.Float('Latitud salida', digits=(16, 5))
    longitude_salida = fields.Float('Longitud salida', digits=(16, 5))
    ubicacion_maps_salida = fields.Char("Ubicación marcaje salida", compute="_compute_ubicacion_maps_salida")

    @api.depends("latitude_entrada", "longitude_entrada")
    def _compute_ubicacion_maps_entrada(self):
        for r in self:
            if r.latitude_entrada and r.longitude_entrada:
                r.ubicacion_maps_entrada = "https://maps.google.com/?q=%s,%s" % (r.latitude_entrada, r.longitude_entrada)
            else:
                r.ubicacion_maps_entrada = False

    @api.depends("latitude_salida", "longitude_salida")
    def _compute_ubicacion_maps_salida(self):
        for r in self:
            if r.latitude_salida and r.longitude_salida:
                r.ubicacion_maps_salida = "https://maps.google.com/?q=%s,%s" % (r.latitude_salida, r.longitude_salida)
            else:
                r.ubicacion_maps_salida = False

    def get_data_api(self):
        self.ensure_one()
        return {
            'id': self.id,
            'check_in': self.check_in and self.check_in.strftime("%d/%m/%Y, %H:%M:%S") or "",
            'check_out': self.check_out and self.check_out.strftime("%d/%m/%Y, %H:%M:%S") or "" ,
        }
