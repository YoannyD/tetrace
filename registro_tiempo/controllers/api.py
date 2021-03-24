# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class RegistroTiempoAPI(http.Controller):
    @http.route('/api/projects', type='json', auth="user", website=True)
    def project_list(self, **kw):
        data = {'data': [], 'totalCount': 0}
        if not request.env.user.employee_ids.ids:
            return json.dumps(data)

        domain = [('employee_id', 'in', request.env.user.employee_ids.ids)]
        search = kw.get('search')
        if search:
            domain += [('project_id.name', 'ilike', search)]

        offset = kw.get('offset') if kw.get('offset') else 0
        limit = kw.get('limit') if kw.get('limit') else 10

        tecnico_calendario = request.env['tetrace.tecnico_calendario'].sudo().search(domain)
        project_ids = [r.project_id.id for r in tecnico_calendario]

        projects = request.env['project.project'].sudo().search([('id', 'in', project_ids)], offset=offset, limit=limit)
        projects_count = request.env['project.project'].sudo().search_count([('id', 'in', project_ids)])
        data['totalCount'] = projects_count
        for project in projects:
            data['data'].append({
                'id': project.id,
                'name': project.name
            })

        return json.dumps(data)

    @http.route('/api/tipo_parada', type='json', auth="user", website=True)
    def tipo_parada_list(self, **kw):
        tipos = request.env["registro_tiempo.tipo_parada"].sudo().search([])
        data = []
        for tipo in tipos:
            data.append(tipo.get_data_api())
        return json.dumps(data)

    @http.route('/api/attendance/start', type='json', auth="user", website=True)
    def attendance_start(self, latitud=False, longitud=False, **kw):
        if not request.env.user.employee_id:
            return json.dumps({
                "result": "ko",
                "msg": "El usuario no es un empleado",
            })

        employee = request.env.user.employee_id
        if employee.attendance_state == "checked_in":
            return json.dumps({
                "result": "ko",
                "msg": "Tiene una entrada en curso.",
            })

        attendance = request.env['hr.attendance'].sudo().create({
            'employee_id': employee.id,
            'check_in': fields.Datetime.now(),
            'latitude_entrada': latitud,
            'longitude_entrada': longitud,
        })

        if attendance:
            return json.dumps({
                "result": "ok",
                "msg": "Entrada realizada correctamente.",
                "attendance": attendance.get_data_api()
            })
        else:
            return json.dumps({
                "result": "ko",
                "msg": "Error al realizar la entrada.",
            })

    @http.route('/api/attendance/stop', type='json', auth="user", website=True)
    def attendance_stop(self, latitud=False, longitud=False, **kw):
        if not request.env.user.employee_id:
            return json.dumps({
                "result": "ko",
                "msg": "El usuario no es un empleado",
            })

        employee = request.env.user.employee_id

        if employee.attendance_state == "checked_out":
            return json.dumps({
                "result": "ko",
                "msg": "No tiene entradas en curso.",
            })

        attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)

        if not attendance:
            return json.dumps({
                "result": "ko",
                "msg": "No tiene entradas en curso.",
            })

        attendance.write({
            'check_out': fields.Datetime.now(),
            'latitude_salida': latitud,
            'longitude_salida': longitud,
        })

        return json.dumps({
            "result": "ok",
            "msg": "Salida realizada correctamente.",
            "attendance": attendance.get_data_api()
        })

    @http.route('/api/time/register', type='json', auth="user", website=True)
    def time_register(self, project_id, **kw):
        try:
            fecha_entrada = fields.Datetime.from_string(kw.get("fecha_entrada"))
        except:
            fecha_entrada = False

        try:
            fecha_salida = fields.Datetime.from_string(kw.get("fecha_salida"))
        except:
            fecha_salida = False

        values = {
            'project_id': project_id,
            "employee_id": request.env.user.employee_id.id,
            "fecha_entrada": fecha_entrada,
            "fecha_salida": fecha_salida,
            "unidades_realizadas": kw.get("unidades_realizadas"),
            "observaciones": kw.get("observaciones")
        }

        tiempo = request.env['registro_tiempo.tiempo'].sudo().create(values)

        if kw.get("paradas"):
            for parada in kw.get("paradas"):
                try:
                    fecha_entrada = fields.Datetime.from_string(kw.get("fecha_entrada"))
                except:
                    fecha_entrada = False

                try:
                    fecha_salida = fields.Datetime.from_string(kw.get("fecha_salida"))
                except:
                    fecha_salida = False

                request.env['registro_tiempo.tiempo_parada'].sudo().create({
                    'tiempo_id': tiempo.id,
                    "tipo_parada_id": parada['tipo_parada_id'],
                    'fecha_entrada': fecha_entrada,
                    'fecha_salida': fecha_salida,
                })

        if tiempo:
            return json.dumps({
                "result": "ok",
                "tiempo": tiempo.get_data_api()
            })
        else:
            return json.dumps({
                "result": "ko",
                "tiempo": {}
            })

    @http.route('/api/festivo', type='json', auth="user", website=True)
    def festivo(self, project_id, fecha, **kw):
        _logger.warning(fecha)
        try:
            fecha = fields.Date.from_string(fecha)
        except:
            fecha = False
        _logger.warning(fecha)
        if not fecha or not request.env.user.employee_ids.ids:
            return json.dumps({"result": "ok"})

        tecnico_calendario = request.env['tetrace.tecnico_calendario'].sudo().search([
            ('project_id', '=', project_id),
            ('employee_id', 'in', request.env.user.employee_ids.ids)
        ], limit=1)

        festivo = False
        if tecnico_calendario:
            festivo = tecnico_calendario.es_festivo(fecha)

        return json.dumps({
            "result": "ok",
            "festivo": festivo
        })
