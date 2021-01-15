# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ITS(models.AbstractModel):
    _name = 'report.tetrace.report_its'
    _description = "Informe previsión de Tesoría (ITS)"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        lineas_por_compania = {}
        for line in lines:
            key = str(line.company_id.id)
            if key not in lineas_por_compania:
                lineas_por_compania.update({
                    key: {
                        'company': line.company_id,
                        'lines': []
                    }
                })

            lineas_por_compania[key]['lines'].append(line)

        for key, data in lineas_por_compania.items():
            report_name = data['company'].name
            sheet = workbook.add_worksheet(report_name[:31])

            data_format1 = workbook.add_format({
                'bg_color': '#800080',
                'color': '#FFFFFF',
                'bold': True
            })
            sheet.set_row(0, cell_format=data_format1)
            sheet.write(0, 5, _("INFORME DE PREVISIÓN DE TESORERÍA"))

            data_format2 = workbook.add_format({
                'bg_color': '#000000',
                'color': '#FFFFFF',
                'bold': True
            })
            sheet.set_row(2, cell_format=data_format2)
            sheet.write(2, 0, _("INSTRUMENTOS DE FINANCIACIÓN"))

            data_format3 = workbook.add_format({
                'bg_color': '#a5a5a5',
                'color': '#800080',
                'bold': True
            })
            sheet.set_row(4, cell_format=data_format3)
            sheet.write(4, 0, _("ANTICIPO DE FRAS"))

            data_format4 = workbook.add_format({
                'bg_color': '#e7f0fd',
                'bold': True
            })
            sheet.set_row(5, cell_format=data_format4)

            sheet.write(5, 0, _("PRÓR"))
            sheet.write(5, 1, _("VCTO"))
            sheet.write(5, 2, _("BANCO"))
            sheet.write(5, 3, _("FRA"))
            sheet.write(5, 4, _("CLIENTE"))
            sheet.write(5, 5, _("IMPORTE"))
            sheet.write(5, 6, _("TOTALES"))
            sheet.write(5, 7, _("TOTALES USD"))

            row = 6
            for line in data['lines']:
                sheet.write(row, 0, 0)
                sheet.write(row, 1, fields.Date.to_string(line.date))
                # sheet.write(row, 2, "BANCO")
                # sheet.write(row, 3, "FRA")
                sheet.write(row, 4, line.partner_id.name)
                sheet.write(row, 5, line.amount_residual)
                # sheet.write(row, 6, "TOTALES")
                # sheet.write(row, 7, "TOTALES USD")
                row += 1
