# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = 'res.users'

    google_gdrive_rtoken = fields.Char('Refresh Token', copy=False)
    google_gdrive_token = fields.Char('User token', copy=False)
    google_gdrive_token_validity = fields.Datetime('Token Validity', copy=False)
    google_gdrive_last_sync_date = fields.Datetime('Last synchro date', copy=False)
