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
        res += ["l10n_ar_afip_responsibility_type_id", "l10n_ar_currency_rate", 
                "invoice_date", "date", "line_ids", "invoice_payment_ref", "invoice_date_due",
                "fecha_servicio", "invoice_payment_term_id", "ref", 'payment_mode_id',
                "partner_id", "fiscal_position_id", "partner_shipping_id", "access_token"]
        return res
    
#     def _check_allow_write_under_validation(self, vals):
#         _logger.warning(vals)
#         return super(TierValidation, self)._check_allow_write_under_validation(vals)