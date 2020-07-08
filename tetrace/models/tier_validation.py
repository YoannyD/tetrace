# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    def write(self, vals):
        state = self._state_field
        state_to = [x for x in self._state_to if x is not None]
        for rec in self:
            if (
                getattr(rec, state) in self._state_from
                and vals.get(self._state_field) in state_to
            ):
                if rec.need_validation:
                    # try to validate operation
                    reviews = rec.request_validation()
                    rec._validate_tier(reviews)
                    if not self._calc_reviews_validated(reviews):
                        raise ValidationError(
                            _(
                                "This action needs to be validated for at least "
                                "one record. \nPlease request a validation."
                            )
                        )
                if rec.review_ids and not rec.validated:
                    raise ValidationError(
                        _(
                            "A validation process is still open for at least "
                            "one record."
                        )
                    )
            if (
                rec.review_ids
                and getattr(rec, self._state_field) in self._state_from
                and not vals.get(self._state_field)
                in (state_to + [self._cancel_state])
                and not self._check_allow_write_under_validation(vals)
            ):
                raise ValidationError(_("The operation is under validation."))
        if vals.get(self._state_field) in self._state_from:
            self.mapped("review_ids").unlink()
        return super(TierValidation, self).write(vals)
