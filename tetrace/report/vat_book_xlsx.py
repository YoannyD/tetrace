# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

from odoo import fields, models
from odoo.tools import ormcache


class VatNumberXlsx(models.AbstractModel):
    _inherit = "report.l10n_es_vat_book.l10n_es_vat_book_xlsx"
    
    def generate_xlsx_report(self, workbook, data, objects):
        new_objects = []
        for object in objects:
            new_objects.append(object.sudo())
        return super(VatNumberXlsx, self).generate_xlsx_report(workbook, data, new_objects)