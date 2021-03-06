# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.tools import image_process

_logger = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = "ir.attachment"

    document_ids = fields.One2many('documents.document', 'attachment_id', string="Documentos")
    document_id = fields.Many2one('documents.document', compute='_compute_document_id', string="Documento")

    @api.depends('document_ids')
    def _compute_document_id(self):
        for p in self:
            p.document_id = p.document_ids[:1].id if p.document_ids else None

    def convert_tiff_to_pdf(self):
        for r in self:
            if r.mimetype != 'image/tiff' and r.type != 'binary' and not r.db_datas:
                continue

            img_png = image_process(r.db_datas, output_format='PNG')
            name = r.name.replace(".TIF", ".png")
            r.write({
                'name': name,
                'db_datas': img_png
            })
