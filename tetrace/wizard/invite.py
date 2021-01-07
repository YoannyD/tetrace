# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Invite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    def add_followers(self):
        return super(Invite, self.with_context(add_follower=True)).add_followers()