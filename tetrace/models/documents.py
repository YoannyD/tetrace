# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _inherit = 'documents.document'

    res_name = fields.Char(store=True)