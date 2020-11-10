# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import re
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    
    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        auto_add_follower = self.env['ir.config_parameter'].sudo().get_param('auto_add_followers', default=False)
        if auto_add_follower:
            return super(MailThread, self).message_subscribe(partner_ids, channel_ids, subtype_ids)
        return True