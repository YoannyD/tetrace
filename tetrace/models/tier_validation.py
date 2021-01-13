# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    @api.model
    def _get_under_validation_exceptions(self):
        res = super(TierValidation, self)._get_under_validation_exceptions()
        res += ["l10n_ar_afip_responsibility_type_id", "l10n_ar_currency_rate"]
        return res
