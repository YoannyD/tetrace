# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http, fields
from odoo.http import request
from odoo.addons.devexpress.models.utils import create_domain, data_groups
from odoo.addons.registro_tiempo.models.date_utils import date_from_string, float_to_time, datetime_from_string, \
    date_str_to_float_time, time_str_to_float

_logger = logging.getLogger(__name__)


class RegistroTiempoAPI(http.Controller):
    @http.route('/api/projects', type='json', auth="user", website=True)
    def project_list(self, **kw):
        data = {'data': [], 'totalCount': 0}
        
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        if not employee:
            return json.dumps(data)
            
        domain = [('employee_id', '=', employee.id)]

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

    @http.route('/api/tecnicos-proyecto', type='json', auth="user", website=True)
    def tecnicos_proyecto_list(self, **kw):
        data = {'data': [], 'totalCount': 0}
        domain = []
        search = kw.get('search')
        if search:
            domain += [('employee_id.name', 'ilike', search)]

        offset = kw.get('offset') if kw.get('offset') else 0
        limit = kw.get('limit') if kw.get('limit') else 10

        tecnicos = request.env['tetrace.tecnico_calendario'].sudo().read_group(
            domain=domain,
            fields=["employee_id"],
            groupby=["employee_id"],
        )

        employee_ids = [int(e['employee_id'][0]) for e in tecnicos]
        employees = request.env['hr.employee'].sudo().search([('id', 'in', employee_ids)], offset=offset, limit=limit, order="name desc")
        data['totalCount'] = len(employee_ids)

        for employee in employees:
            data['data'].append({
                'id': employee.id,
                'name': employee.name
            })

        return json.dumps(data)

    @http.route('/api/tipo_parada', type='json', auth="user", website=True)
    def tipo_parada_list(self, **kw):
        tipos = request.env["registro_tiempo.tipo_parada"].sudo().search([])
        data = []
        for tipo in tipos:
            data.append(tipo.get_data_api())
        return json.dumps(data)
    
    @http.route('/api/time-data/<int:tiempo_id>', type='json', auth="user", website=True)
    def datos_tiempo(self, tiempo_id, **kw):
        tiempo = request.env["registro_tiempo.tiempo"].sudo().browse(tiempo_id)
        data = tiempo.get_data_api()
        return json.dumps(data)

    @http.route('/api/attendance/start', type='json', auth="user", website=True)
    def attendance_start(self, latitud=False, longitud=False, **kw):
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        if not employee:
            return json.dumps({
                "result": "ko",
                "msg": "El usuario no es un empleado",
            })

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
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        
        if not employee:
            return json.dumps({
                "result": "ko",
                "msg": "El usuario no es un empleado",
            })

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

    @http.route('/api/registros', type='json', auth="user", website=True)
    def registros_list(self, filtros=None, project_id=None, order=None, offset=None, limit=None,
                       group=None, **kw):
        data = {'data': [], 'totalCount': 0}
        
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        if not employee:
            return json.dumps(data)

        offset = offset or 0
        limit = limit or 10
        order = order or "id desc"

        domain = create_domain(filtros)
        domain += [('employee_id', '=', employee.id)]

        if project_id:
            domain += [('project_id', '=', project_id)]

        if group:
            data = data_groups("registro_tiempo.tiempo", group, domain, 0)
        else:
            Tiempo = request.env["registro_tiempo.tiempo"].sudo()
            tiempos = Tiempo.search(domain, offset=offset, limit=limit, order=order)
            tiempos_count = Tiempo.search_count(domain)
            data['totalCount'] = tiempos_count

            for tiempo in tiempos:
                data['data'].append(tiempo.get_data_api())
        return json.dumps(data)

    @http.route('/api/time/register', type='json', auth="user", website=True)
    def time_register(self, **kw):
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        
        values = self.parse_values_tiempo(kw)
        _logger.warning(values)
        tiempo = request.env['registro_tiempo.tiempo'].sudo().create(values)
        
        values = {
            'horas_extra': tiempo.get_horas_extra(),
            'horas_extra_cliente': tiempo.get_horas_extra_cliente(),
        }
        if tiempo.es_festivo():
            values.update({'festivo': True})

        if tiempo.es_festivo_cliente():
            values.update({'festivo_cliente': True})

        if tiempo.es_nocturno():
            values.update({'nocturno': True})

        if tiempo.tipo == 'parte':
            values.update({'unidades_realizadas': kw.get("unidades_realizadas")})

        if values:
            tiempo.write(values)

        if tiempo.tipo == 'parte' and kw.get("paradas"):
            for parada in kw.get("paradas"):
                fecha_entrada = datetime_from_string(parada['fecha_entrada'])
                fecha_salida = datetime_from_string(parada['fecha_salida'])

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

    @http.route('/api/time/edit/<int:tiempo_id>', type='json', auth="user", website=True)
    def time_edit(self, tiempo_id, **kw):
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        tiempo = request.env['registro_tiempo.tiempo'].sudo().browse(tiempo_id)
        
        values = self.parse_values_tiempo(kw)
        tiempo.write(values)
        
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
        
    def parse_values_tiempo(self, params):
        fecha_entrada = date_from_string(params.get("fecha_entrada"))
        try:
            hora_entrada = time_str_to_float(params.get("hora_entrada"))
        except:
            hora_entrada = 0

        fecha_salida = date_from_string(params.get("fecha_salida"))
        try:
            hora_salida = time_str_to_float(params.get("hora_salida"))
        except:
            hora_salida = 0
            
        values = {
            'project_id': params.get('project_id'),
            'employee_id': request.env.user.employee_ids[0].id if request.env.user.employee_ids else None,
            "tipo": params.get("tipo").lower() if params.get("tipo") else None,
            "fecha_entrada": fecha_entrada,
            "hora_entrada": hora_entrada,
            "fecha_salida": fecha_salida,
            "hora_salida": hora_salida,
            "observaciones": params.get("observaciones"),
            "tareas": params.get("tareas"),
            "covid": params.get("covid")
        }
        return values
    
    @http.route('/api/festivo', type='json', auth="user", website=True)
    def festivo(self, project_id, fecha, **kw):
        fecha = date_from_string(fecha)
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        if not fecha or not employee:
            return json.dumps({"result": "ok"})
        
        tecnico_calendario = request.env['tetrace.tecnico_calendario'].sudo().search([
            ('project_id', '=', project_id),
            ('employee_id', '=', employee.id),
            ('resource_calendar_id', '!=', False)
        ], limit=1)

        festivo = False
        if tecnico_calendario:
            festivo = tecnico_calendario.resource_calendar_id.es_festivo(fecha)

        return json.dumps({
            "result": "ok",
            "festivo": festivo
        })

    @http.route('/api/calendario/hora_dia_semana', type='json', auth="user", website=True)
    def calendario_hora_inicio(self, project_id, fecha, **kw):
        fecha = date_from_string(fecha)
        desde_hora, desde_min = 0, 0
        hasta_hora, hasta_min = 0, 0

        if fecha:
            employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
            tecnico_calendario = request.env['tetrace.tecnico_calendario'].sudo().search([
                ('project_id', '=', project_id),
                ('employee_id', '=', employee.id)
            ], limit=1)

            if tecnico_calendario:
                attendance = request.env["resource.calendar.attendance"].search([
                    ('calendar_id', '=', tecnico_calendario.resource_calendar_id.id),
                    ('dayofweek', '=', fecha.weekday()),
                ], limit=1)

                if attendance.hour_from:
                    hour_time = float_to_time(attendance.hour_from)
                    desde_hora = hour_time.strftime("%H")
                    desde_min = hour_time.strftime("%M")

                if attendance.hour_to:
                    hour_time = float_to_time(attendance.hour_to)
                    hasta_hora = hour_time.strftime("%H")
                    hasta_min = hour_time.strftime("%M")

        return json.dumps({
            "result": "ok",
            "desde_hora": int(desde_hora),
            "desde_min": int(desde_min),
            "hasta_hora": int(hasta_hora),
            "hasta_min": int(hasta_min),
        })
