# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _inherit = 'documents.document'

    res_name = fields.Char(store=True, compute="_compute_res_name")
    
    @api.depends("res_id", "res_model")
    def _compute_res_name(self):
        for r in self:
            name = False
            if r.res_id and r.res_model:
                record = self.env[r.res_model].browse(r.res_id)
                if record:
                    name = record.name
            r.res_name = name