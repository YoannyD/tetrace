# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from .aep import AccountingExpressionProcessor as AEP

_logger = logging.getLogger(__name__)


class MisReport(models.Model):
    _inherit = 'mis.report'

    def _prepare_aep(self, companies, currency=None, informe_fecha_contable=False):
        self.ensure_one()
        aep = AEP(companies, currency, self.account_model, informe_fecha_contable)
        for kpi in self.all_kpi_ids:
            for expression in kpi.expression_ids:
                if expression.name:
                    aep.parse_expr(expression.name)
        aep.done_parsing()
        return aep
