# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import base64
import io
import tempfile
import binascii
import xlrd

from odoo import models, fields, api, _
from datetime import datetime

_logger = logging.getLogger(__name__)


class ImportarNonmina(models.TransientModel):
    _name = 'tetrace.importar_nomina'
    _description = 'Importar nóminas'

    nomina_id = fields.Many2one('tetrace.nomina', string="Nómina", ondelete="cascade", required=True)
    company_id = fields.Many2one(related='nomina_id.company_id')
    file = fields.Binary('File')
    import_option = fields.Selection([
        ('dat', _('DAT File')), 
        ('xls', _('XLS File'))
    ], string='Selecciona', required=True, default='dat')

    def action_import(self):
        self.ensure_one()
        self.nomina_id.nomina_trabajador_ids.unlink()
        if self.import_option == "dat":
            self.import_dat_file()
        elif self.import_option == "xls":
            self.import_xls_file()
            
    def import_xls_file(self):
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(sheet.nrows):   
            if row_no <= 0:
                fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                if len(line) >= 8:
                    employee = self.env['hr.employee'].search([
                        ('codigo_trabajador_company', '=', line[6]),
                        ('company_id', '=', self.company_id.id)
                    ], limit=1)
                    
                    account = self.env['account.account'].search([
                        ('code', '=', line[4]),
                        ('company_id', '=', self.company_id.id)
                    ], limit=1)
                    
                    try:
                        fecha_inicio = datetime.strptime(line[2], '%Y-%m-%d')
                    except:
                        fecha_inicio = None
                        
                    try:
                        fecha_fin = datetime.strptime(line[3], '%Y-%m-%d')
                    except:
                        fecha_fin = None
                    
                    try:
                        debe = float(line[7])
                    except:
                        debe = 0.0
                        
                    try:
                        haber = float(line[8])
                    except:
                        haber = 0.0
                    
                    values = {
                        'nomina_id': self.nomina_id.id,
                        'employee_id': employee.id,
                        'account_id': account.id,
                        'fecha_inicio': fecha_inicio,
                        'fecha_fin': fecha_fin,
                        'descripcion': line[5],
                        'debe': debe,
                        'haber': haber,
                    }
             
                    nomina_trabajador = self.env['tetrace.nomina.trabajador'].create(values)
                    nomina_trabajador.generar_distribucion_analitica()
                else:
                    raise Warning(_('Your File has less column please refer sample file'))
            
    def import_dat_file(self):
        data = base64.b64decode(self.file)
        data_file = io.StringIO(data.decode('iso-8859-1'))
        data_file.seek(0)
        lineas = data_file.readlines()

        for linea in lineas:
            linea = linea.encode('utf8').decode('utf8')
            ano = linea[6:10]
            mes = linea[10:12]
            dia = int(linea[12:14])
            fecha_inicio = "%s-%s-01" % (ano, mes)
            fecha_fin = "%s-%s-%s" % (ano, mes, dia)

            cuenta = linea[15:23].strip()
            account = self.env['account.account'].search([
                ('code', '=', cuenta),
                ('company_id', '=', self.company_id.id)
            ], limit=1)

            descripcion = linea[27:57].strip()
            debe_haber = linea[57:58].strip()
            
            importe = linea[99:113].strip()
            importe_calculo = float(importe)
            if importe_calculo > 0:
                debe = importe if debe_haber == 'D' else 0
                haber = importe if debe_haber == 'H' else 0
            elif importe_calculo < 0:
                debe = str(abs(importe_calculo)) if debe_haber == 'H' else 0
                haber = str(abs(importe_calculo)) if debe_haber == 'D' else 0
                
            employee = False
            key_trabajador = linea[58:66].strip()
            if key_trabajador:
                employee = self.env['hr.employee'].search([
                    ('codigo_trabajador_company', '=', key_trabajador[-6:]),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)

            values_nomina_trabajador = {
                'nomina_id': self.nomina_id.id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'employee_id': employee.id if employee else None,
                'account_id': account.id if account else None,
                'descripcion': descripcion,
                'debe': debe,
                'haber': haber,
                'texto_importado': linea
            }

            nomina_trabajador = self.env['tetrace.nomina.trabajador'].create(values_nomina_trabajador)
            nomina_trabajador.generar_distribucion_analitica()

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
