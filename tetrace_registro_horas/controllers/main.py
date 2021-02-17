# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import http
from odoo.http import request, Controller
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class ControlHoras(Controller):
    @http.route('/my/timesheet', type='http', auth="user")
    def home_parte_horas(self, **kwargs):
        projects = request.env['project.project'].sudo().search([])
        values = {
            'projects': projects
        }
        return request.render("tetrace_registro_horas.home_parte_horas", values)
