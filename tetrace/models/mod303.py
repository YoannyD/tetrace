# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.addons.l10n_es_aeat_mod303.models.mod303 import _ACCOUNT_PATTERN_MAP

_logger = logging.getLogger(__name__)


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"
    
    @api.depends("company_id", "result_type")
    def _compute_counterpart_account_id(self):
        for record in self:
            code = ("%s%%" % _ACCOUNT_PATTERN_MAP.get(record.result_type, "4750"),)
            record.counterpart_account_id = self.env["account.account"].search(
                [("code", "=like", code[0]), ("company_id", "=", record.company_id.id)],
                limit=1,
            )