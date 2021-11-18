# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class RegistroHoras(CustomerPortal):
    @http.route('/my/timesheet', type='http', auth="user", website=True)
    def home_parte_horas(self, **kwargs):
        tipos_parada = request.env["registro_tiempo.tipo_parada"].sudo().search([])
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        values = {
            'employee': employee,
            'tipos_parada': tipos_parada
        }
        return request.render("registro_tiempo.home_parte_horas", values)
    
    @http.route('/my/timesheet/<int:tiempo_id>', type='http', auth="user", website=True)
    def ficha_parte_horas(self, tiempo_id, **kwargs):
        tiempo = request.env['registro_tiempo.tiempo'].sudo().browse(tiempo_id)
        tipos_parada = request.env["registro_tiempo.tipo_parada"].sudo().search([])
        employee = request.env.user.employee_ids[0] if request.env.user.employee_ids else None
        values = {
            'employee': employee,
            'tipos_parada': tipos_parada,
            'tiempo': tiempo
        }
        return request.render("registro_tiempo.ficha_parte_horas", values)
