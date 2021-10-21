# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ModifyReference(models.TransientModel):
    _name = 'modify.reference'

    def modify(self):
        applicants = self.env['hr.applicant'].sudo().search([])
        for applicant in applicants:
            applicant.reference = "P" + str(applicant.id + 1)
        return {'type': 'ir.actions.act_window_close'}
