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
FILTROS_ESTRUCTURALES = [
    ('todos', _("Incluir todos")),
    ('sin', _("Sin estructurales")),
    ('con', _("Solo estructurales")),
]


class MisReportInstance(models.Model):
    _inherit = 'mis.report.instance'

    informe_fecha_contable = fields.Boolean('Informe con fecha contable')
    informe_con_cuentas_analiticas = fields.Boolean("Generar pestaña por cuenta analítica con datos")
    filtro_estructurales = fields.Selection(FILTROS_ESTRUCTURALES, string=_("Filtro estructurales"))
    filtro_estado_cuentas_analiticas = fields.Selection([
        ('todos', _("Todos")),
        ('cerradas', _("Cerradas")),
        ('abiertas', _("Abiertas")),
    ], string="Filtro estado cuenta analítica")
    tipo_proyecto_id = fields.Many2one('tetrace.tipo_proyecto', string="Tipo de proyecto", 
                                       context='{"display_tipo": True}')

    def _add_analytic_filters_to_context(self, context):
        super(MisReportInstance, self)._add_analytic_filters_to_context(context)
        if self.filtro_estructurales in ['sin', 'con']:
            context["mis_report_filters"]["analytic_account_id.estructurales"] = {
                "value": True if self.filtro_estructurales == 'con' else False,
                "operator": "=",
            }
            
        if self.filtro_estado_cuentas_analiticas in ['cerradas', 'abiertas']:
            context["mis_report_filters"]["analytic_account_id.analitica_cerrada"] = {
                "value": True if self.filtro_estado_cuentas_analiticas == 'cerradas' else False,
                "operator": "=",
            }
            
        if self.tipo_proyecto_id:
            context["mis_report_filters"]["analytic_account_id.project_ids.sale_order_id.tipo_proyecto_id"] = {
                "value": self.tipo_proyecto_id.id,
                "operator": "=",
            }
            
    def _compute_matrix(self):
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
