# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import base64
import io
import tempfile
import binascii
import xlrd

from datetime import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ImportarTickelia(models.TransientModel):
    _name = 'tetrace.importar_tickelia'
    _description = 'Importar Tickelia'

    tickelia_id = fields.Many2one('tetrace.tickelia', string="Tickelia", ondelete="cascade", required=True)
    company_id = fields.Many2one(related='tickelia_id.company_id')
    file = fields.Binary('XLXS File')

    def action_import_from_excel(self):
        self.ensure_one()
        self.tickelia_id.tickelia_trabajador_ids.unlink()
        company_id = self.company_id.id
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))

                if len(line) == 66:
                    cuenta_contrapartida = line[63] if line[63]!='' else line[64]
                    values = {
                        'tickelia_id': self.tickelia_id.id,
                        'fecha': datetime(*xlrd.xldate_as_tuple(float(line[14]),0)),
                        'employee_id': self.env['hr.employee'].sudo().search([('identification_id', '=', line[0]),('company_id','=',company_id)],limit=1).id,
                        'cuenta_gasto': self.env['account.account'].search([
                            ('code', '=', line[6]),
                            ('company_id', '=', company_id)
                        ], limit=1).id,
                        'cuenta_contrapartida': self.env['account.account'].search([
                            ('code', '=', cuenta_contrapartida),
                            ('company_id', '=', company_id)
                        ], limit=1).id,
                        'descripcion': line[11],
                        'importe': line[20],
                        'cuenta_analitica_id': self.env['account.analytic.account'].search([('code', '=like', line[43]),'|', ('company_id', '=', False), ('company_id', '=', company_id)], limit=1).id,
                        'liquidacion': line[31].split('.')[0],
                        'fecha_liquidacion': datetime(*xlrd.xldate_as_tuple(float(line[32]),0)),
                    }
                    _logger.warning(values)
                    tickelia_trabajador = self.env['tetrace.tickelia.trabajador'].create(values)
                elif len(line) > 66:
                    raise Warning(_('Your File has extra column please refer sample file'))
                else:
                    raise Warning(_('Your File has less column please refer sample file'))

        return {'type': 'ir.actions.act_window_close'}


    def open_wizard(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }
