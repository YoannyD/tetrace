# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import base64
import io

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ImportarNonmina(models.TransientModel):
    _name = 'tetrace.importar_nomina'
    _description = 'Importar nóminas'

    nomina_id = fields.Many2one('tetrace.nomina', string="Nómina", ondelete="cascade", required=True)
    file = fields.Binary('File')

    def action_import(self):
        self.ensure_one()
        data = base64.b64decode(self.file)
        data_file = io.StringIO(data.decode("ISO-8859-1"))
        data_file.seek(0)
        lineas = data_file.readlines()

        for linea in lineas:
            ano = linea[6:10]
            mes = linea[10:12]
            dia = linea[12:14]
            fecha_inicio = "%s-%s-01" % (ano, mes)
            fecha_fin = "%s-%s-%s" % (ano, mes, dia)
            cuenta = linea[15:23].strip()
            account = self.env['account.account'].search([('code', '=', cuenta)], limit=1)

            descripcion = linea[27:57].strip()
            debe_haber = linea[57:58].strip()
            importe = linea[99:113].strip()
            debe = importe if debe_haber == 'D' else 0
            haber = importe if debe_haber == 'H' else 0

            key_trabajador = linea[58:66].strip()
            employee = self.env['hr.employee'].search([('key_nomina', '=', key_trabajador)], limit=1)

            NominaTrabajador = self.env['tetrace.nomina.trabajador']
            nomina_trabajador = NominaTrabajador.search([
                ('nomina_id', '=', self.nomina_id.id),
                ('employee_id', '=', employee.id if employee else None),
                ('account_id', '=', account.id if account else None),
                ('fecha_inicio', '=', fecha_inicio),
                ('fecha_fin', '=', fecha_fin),
                ('debe', '=', debe),
                ('haber', '=', haber)
            ])

            values_nomina_trabajador = {
                'nomina_id': self.nomina_id.id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'employee_id': employee.id if employee else None,
                'account_id': account.id if account else None,
                'descripcion': descripcion,
                'debe': importe if debe_haber == 'D' else 0,
                'haber': importe if debe_haber == 'H' else 0,
            }

            if nomina_trabajador:
                nomina_trabajador.write(values_nomina_trabajador)
            else:
                nomina_trabajador = NominaTrabajador.create(values_nomina_trabajador)
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
