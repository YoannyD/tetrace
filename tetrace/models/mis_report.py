# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from .kpimatrix import KpiMatrix
from .aep import AccountingExpressionProcessor as AEP

_logger = logging.getLogger(__name__)


class MisReport(models.Model):
    _inherit = 'mis.report'

    mostrar_cuenta_consolidacion = fields.Boolean('Mostrar cuenta consolidación')
    
    def _prepare_aep(self, companies, currency=None, informe_fecha_contable=False):
        self.ensure_one()
        aep = AEP(companies, currency, self.account_model, informe_fecha_contable)
        for kpi in self.all_kpi_ids:
            for expression in kpi.expression_ids:
                if expression.name:
                    aep.parse_expr(expression.name)
        aep.done_parsing()
        return aep
    
    def prepare_kpi_matrix(self, multi_company=False):
        self.ensure_one()
        kpi_matrix = KpiMatrix(self.env, multi_company, self.account_model)
        kpi_matrix.mostrar_cuenta_consolidacion = self.mostrar_cuenta_consolidacion
        for kpi in self.kpi_ids:
            kpi_matrix.declare_kpi(kpi)
        return kpi_matrix
