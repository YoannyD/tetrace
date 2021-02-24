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
        projects = request.env['project.project'].sudo().search([])
        tipos_parada = request.env["registro_tiempo.tipo_parada"].sudo().search([])
        values = {
            'employee': request.env.user.employee_id,
            'projects': projects,
            'tipos_parada': tipos_parada
        }
        return request.render("registro_tiempo.home_parte_horas", values)
