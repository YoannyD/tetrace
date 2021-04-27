# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo.addons.mis_builder.models.kpimatrix import KpiMatrix

_logger = logging.getLogger(__name__)


def _get_account_name(self, account):
    if self.mostrar_cuenta_consolidacion and account.tetrace_account_id:
        result = account.tetrace_account_id.name
    else:
        result = u"{} {}".format(account.code, account.name)
        
    if self._multi_company:
        result = u"{} [{}]".format(result, account.company_id.name)
    return result

KpiMatrix._get_account_name = _get_account_name
KpiMatrix.mostrar_cuenta_consolidacion = False