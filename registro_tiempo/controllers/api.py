# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http, fields
from odoo.http import request
from odoo.addons.registro_tiempo.models import date_utils

_logger = logging.getLogger(__name__)


class RegistroTiempoAPI(http.Controller):
    @http.route('/api/projects', type='json', auth="user", website=True)
    def project_list(self, **kw):
        domain = []
        _logger.warning(kw)
        search = kw.get('search')
        if search:
            domain += [('name', 'ilike', search)]

        offset = kw.get('offset') if kw.get('offset') else 0
        limit = kw.get('limit') if kw.get('limit') else 10
        _logger.warning(domain)
        projects = request.env['project.project'].sudo().search(domain, offset=offset, limit=limit)
        projects_count = request.env['project.project'].sudo().search_count(domain)
        data = {'data': [], 'totalCount': projects_count}
        for project in projects:
            data['data'].append({
                'id': project.id,
                'name': project.name
            })
        _logger.warning(data)
        return json.dumps(data)

    @http.route('/api/time/register', type='json', auth="user", website=True)
    def time_register(self, project_id, **kw):
        _logger.warning(kw)

        fecha = False
        if kw.get("fecha"):
            try:
                f = kw.get("fecha").split(" ")
                fecha = fields.Date.from_string(f[0])
            except:
                fecha = False

        hora_inicio = hora_inicio = date_utils.date_str_to_float_time(kw.get("hora_inicio"))
        if kw.get("hora_inicio"):
            try:
                hora_inicio = date_utils.date_str_to_float_time(kw.get("hora_inicio"))
            except:
                hora_inicio = False

        hora_fin = False
        if kw.get("hora_fin"):
            try:
                hora_fin = date_utils.date_str_to_float_time(kw.get("hora_fin"))
            except:
                hora_fin = False

        values = {
            'project_id': project_id,
            "employee_id": request.env.user.employee_id.id,
            "fecha": fecha,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "unidades_realizadas": kw.get("unidades_realizadas"),
            "observaciones": kw.get("observaciones")
        }

        tiempo = request.env['registro_tiempo.tiempo'].sudo().create(values)

        if kw.get("paradas"):
            for parada in kw.get("paradas"):
                try:
                    hora_fin = date_utils.date_str_to_float_time(kw.get("hora_fin"))
                except:
                    hora_fin = False

                try:
                    hora_inicio = date_utils.date_str_to_float_time(kw.get("hora_inicio"))
                except:
                    hora_inicio = False

                request.env['registro_tiempo.tiempo_parada'].sudo().create({
                    'tiempo_id': tiempo.id,
                    "name": parada['tipo_parada'],
                    'hora_inicio': hora_inicio,
                    'hora_fin': hora_fin,
                })

        return json.dumps({
            "result": "ok",
            "tiempo": self.get_tiempo_data(tiempo)
        })

    @http.route('/api/time/start', type='json', auth="user", website=True)
    def time_start(self, project_id, **kw):
        Tiempo = request.env['registro_tiempo.tiempo'].sudo()
        tiempo = Tiempo.search([
            ("project_id", '=', project_id),
            ("employee_id", "=", request.env.user.employee_id.id),
            ('hora_fin', '=', False)
        ], limit=1)

        if tiempo:
            return json.dumps({
                "result": "ko",
                "tiempo": self.get_tiempo_data(tiempo)
            })

        hora_actual = fields.Datetime.now().strftime("%H:%M")
        tiempo = request.env['registro_tiempo.tiempo'].sudo().create({
            'project_id': project_id,
            'employee_id': request.env.user.employee_id.id,
            'fecha': fields.Date.today(),
            'hora_inicio': date_utils.time_str_to_float(hora_actual)
        })

        return json.dumps({
            "result": "ok",
            "tiempo": self.get_tiempo_data(tiempo)
        })

    @http.route('/api/time/stop', type='json', auth="user", website=True)
    def time_stop(self, project_id, **kw):
        Tiempo = request.env['registro_tiempo.tiempo'].sudo()
        tiempo = Tiempo.search([
            ("project_id", '=', project_id),
            ("employee_id", "=", request.env.user.employee_id.id),
            ('fecha', '!=', False),
            ('hora_inicio', '!=', False),
            ('hora_fin', '=', False),
        ], limit=1)
        if tiempo:
            hora_actual = fields.Datetime.now().strftime("%H:%M")
            tiempo.write({"hora_fin": date_utils.time_str_to_float(hora_actual)})
            return json.dumps({
                "result": "ok",
                "tiempo": self.get_tiempo_data(tiempo)
            })

        return json.dumps({
            "result": "ko",
            "tiempo": {}
        })

    def get_tiempo_data(self, tiempo):
        values = {
            'id': tiempo.id,

        }
        return values


