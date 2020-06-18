# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.tools import image_process

_logger = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = "ir.attachment"

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
