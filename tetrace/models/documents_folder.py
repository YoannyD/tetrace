# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class DocumentFolder(models.Model):
    _inherit = 'documents.folder'
    
    view_employee = fields.Boolean("Portal empleado")
    view_all = fields.Boolean("Portal todos empleados")