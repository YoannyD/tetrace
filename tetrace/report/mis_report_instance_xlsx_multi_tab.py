# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import numbers
from collections import defaultdict
from datetime import datetime

from odoo import _, fields, models

from odoo.addons.mis_builder.models.accounting_none import AccountingNone
from odoo.addons.mis_builder.models.data_error import DataError
from odoo.addons.mis_builder.models.mis_report_style import TYPE_STR

_logger = logging.getLogger(__name__)


ROW_HEIGHT = 15  # xlsxwriter units
COL_WIDTH = 0.9  # xlsxwriter units
MIN_COL_WIDTH = 10  # characters
MAX_COL_WIDTH = 50  # characters

    
class MisBuilderXlsxMultiTab(models.AbstractModel):
    _name = "report.tetrace.mis_report_instance_xlsx_multi_tab"
    _description = "MIS Builder XLSX report Multi Tab"
    _inherit = "report.report_xlsx.abstract"
    
    def generate_xlsx_report(self, workbook, data, objects, offset=0, limit=50):
        # create worksheet
        report_name = u"{} - {}".format(
            objects[0].name, u", ".join([a.name for a in objects[0].query_company_ids])
        )

        grupo_cuentas = self.env['account.analytic.line.rel'].read_group([], ['analytic_account_id'], ['analytic_account_id'])
        
        cuentas = []
        for cuenta in grupo_cuentas:
            cuentas.append(cuenta.get('analytic_account_id')[0])
        
        domain = [('id', 'in', cuentas)]
        if objects[0].filtro_estado_cuentas_analiticas:
            domain += [('analitica_cerrada', '=', True if objects[0].filtro_estado_cuentas_analiticas == 'cerradas' else False)]
            
        if objects[0].tipo_proyecto_id:
            domain += [('project_ids.sale_order_id.tipo_proyecto_id', '=', objects[0].tipo_proyecto_id.id)]
        
        analitycs = self.env['account.analytic.account'].search(domain, offset=offset, limit=limit, order="id asc")
        
        for analityc in analitycs:
            condition = {
                'analytic_account_id': {
                    'value': analityc.id, 
                    'operator': '='
                }
            }

            self.env.context = dict(self.env.context, mis_report_filters=condition)
            data['context'].update({'mis_report_filters': condition})
            creada = self.tab_anlitica(workbook, data, objects, analityc)
        
    def tab_anlitica(self, workbook, data, objects, analityc):
        # get the computed result of the report
        matrix = objects._compute_matrix()
        
        hay_datos = False
        for row in matrix.iter_rows():
            if hay_datos:
                break
            for cell in row.iter_cells():
                if not cell or cell.val is None or cell.val is AccountingNone or cell.val == 0.0:
                    continue
                hay_datos = True
                break
                
        if not hay_datos:
            return False
            
        _logger.warning("Nueva pestaña")
        style_obj = self.env["mis.report.style"]
        
        nombre_pestana = "%s - %s" % (analityc.id, analityc.name)
        sheet = workbook.add_worksheet(nombre_pestana[:31])
        
        row_pos = 0
        col_pos = 0
        # width of the labels column
        label_col_width = MIN_COL_WIDTH
        # {col_pos: max width in characters}
        col_width = defaultdict(lambda: MIN_COL_WIDTH)

        # document title
        bold = workbook.add_format({"bold": True})
        header_format = workbook.add_format(
            {"bold": True, "align": "center", "bg_color": "#F0EEEE"}
        )

        # filters
        if not objects.hide_analytic_filters:
            for filter_description in objects.get_filter_descriptions_from_context():
                sheet.write(row_pos, 0, filter_description, bold)
                row_pos += 1
            row_pos += 1

        # column headers
        sheet.write(row_pos, 0, "", header_format)
        col_pos = 1
        for col in matrix.iter_cols():
            label = col.label
            if col.description:
                label += "\n" + col.description
                sheet.set_row(row_pos, ROW_HEIGHT * 2)
            if col.colspan > 1:
                sheet.merge_range(
                    row_pos,
                    col_pos,
                    row_pos,
                    col_pos + col.colspan - 1,
                    label,
                    header_format,
                )
            else:
                sheet.write(row_pos, col_pos, label, header_format)
                col_width[col_pos] = max(
                    col_width[col_pos], len(col.label or ""), len(col.description or "")
                )
            col_pos += col.colspan
        row_pos += 1

        # sub column headers
        sheet.write(row_pos, 0, "", header_format)
        col_pos = 1
        for subcol in matrix.iter_subcols():
            label = subcol.label
            if subcol.description:
                label += "\n" + subcol.description
                sheet.set_row(row_pos, ROW_HEIGHT * 2)
            sheet.write(row_pos, col_pos, label, header_format)
            col_width[col_pos] = max(
                col_width[col_pos],
                len(subcol.label or ""),
                len(subcol.description or ""),
            )
            col_pos += 1
        row_pos += 1

        # rows
        for row in matrix.iter_rows():
            if (
                row.style_props.hide_empty and row.is_empty()
            ) or row.style_props.hide_always:
                continue
            row_xlsx_style = style_obj.to_xlsx_style(TYPE_STR, row.style_props)
            row_format = workbook.add_format(row_xlsx_style)
            col_pos = 0
            label = row.label
            if row.description:
                label += "\n" + row.description
                sheet.set_row(row_pos, ROW_HEIGHT * 2)
            sheet.write(row_pos, col_pos, label, row_format)
            label_col_width = max(
                label_col_width, len(row.label or ""), len(row.description or "")
            )
            for cell in row.iter_cells():
                col_pos += 1
                if not cell or cell.val is AccountingNone:
                    # TODO col/subcol format
                    sheet.write(row_pos, col_pos, "", row_format)
                    continue
                cell_xlsx_style = style_obj.to_xlsx_style(
                    cell.val_type, cell.style_props, no_indent=True
                )
                cell_xlsx_style["align"] = "right"
                cell_format = workbook.add_format(cell_xlsx_style)
                if isinstance(cell.val, DataError):
                    val = cell.val.name
                    # TODO display cell.val.msg as Excel comment?
                elif cell.val is None or cell.val is AccountingNone:
                    val = ""
                else:
                    divider = float(cell.style_props.get("divider", 1))
                    if (
                        divider != 1
                        and isinstance(cell.val, numbers.Number)
                        and not cell.val_type == "pct"
                    ):
                        val = cell.val / divider
                    else:
                        val = cell.val
                sheet.write(row_pos, col_pos, val, cell_format)
                col_width[col_pos] = max(
                    col_width[col_pos], len(cell.val_rendered or "")
                )
            row_pos += 1

        # Add date/time footer
        row_pos += 1
        footer_format = workbook.add_format(
            {"italic": True, "font_color": "#202020", "size": 9}
        )
        lang_model = self.env["res.lang"]
        lang = lang_model._lang_get(self.env.user.lang)

        now_tz = fields.Datetime.context_timestamp(
            self.env["res.users"], datetime.now()
        )
        create_date = _("Generated on {} at {}").format(
            now_tz.strftime(lang.date_format), now_tz.strftime(lang.time_format)
        )
        sheet.write(row_pos, 0, create_date, footer_format)

        # adjust col widths
        sheet.set_column(0, 0, min(label_col_width, MAX_COL_WIDTH) * COL_WIDTH)
        data_col_width = min(MAX_COL_WIDTH, max(col_width.values()))
        min_col_pos = min(col_width.keys())
        max_col_pos = max(col_width.keys())
        sheet.set_column(min_col_pos, max_col_pos, data_col_width * COL_WIDTH)
        return True