# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

MODE_NONE = "none"
SRC_ACTUALS = "actuals"
SRC_ACTUALS_ALT = "actuals_alt"
SRC_CMPCOL = "cmpcol"
SRC_SUMCOL = "sumcol"


class MisReportInstance(models.Model):
    _inherit = 'mis.report.instance'

    informe_fecha_contable = fields.Boolean('Informe con fecha contable')
    informe_con_cuentas_analiticas = fields.Boolean("Generar pestaña por cuenta analítica con datos")
    estructurales = fields.Boolean("Incluir estructurales")
    filtro_estructurales = fields.Boolean("Utilizar filtro estructurales")

    def _add_analytic_filters_to_context(self, context):
        self.ensure_one()
        super(MisReportInstance, self)._add_analytic_filters_to_context(context)
        if self.filtro_estructurales and not self.estructurales:
            context["mis_report_filters"]["analytic_account_id.estructurales"] = {
                "value": False,
                "operator": "=",
            }
    
    def _compute_matrix(self):
        self.ensure_one()
        aep = self.report_id._prepare_aep(self.query_company_ids, self.currency_id, self.informe_fecha_contable)
        kpi_matrix = self.report_id.prepare_kpi_matrix(self.multi_company)
        for period in self.period_ids:
            description = None
            if period.mode == MODE_NONE:
                pass
            elif not self.display_columns_description:
                pass
            elif period.date_from == period.date_to and period.date_from:
                description = self._format_date(period.date_from)
            elif period.date_from and period.date_to:
                date_from = self._format_date(period.date_from)
                date_to = self._format_date(period.date_to)
                description = _("from %s to %s") % (date_from, date_to)

            self._add_column(aep, kpi_matrix, period, period.name, description)
        kpi_matrix.compute_comparisons()
        kpi_matrix.compute_sums()
        return kpi_matrix
    
    def export_xls(self):
        self.ensure_one()
        context = dict(self._context_with_filters())
        if self.informe_con_cuentas_analiticas:
            report = self.env.ref("tetrace.xls_export_multi_tab")
        else:
            report = self.env.ref("mis_builder.xls_export")
        
        return (
            report
            .with_context(context)
            .report_action(self, data=dict(dummy=True))  # required to propagate context
        )
