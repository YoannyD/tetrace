# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import re
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    
    @api.model
    def create(self, vals):
        context = dict(self.env.context)
        auto_add_follower = self.env['ir.config_parameter'].sudo().get_param('auto_add_followers', default=False)
        if not auto_add_follower:
            context.update({
                "mail_create_nosubscribe": True,
                "add_follower": False
            })
        else:
            context.update({"add_follower": True})

        self = self.with_context(context)
        return super(MailThread, self).create(vals)
    
    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        context = dict(self.env.context)
        context.update({"add_follower": True})
        self = self.with_context(context)
        return super(MailThread, self).message_subscribe(partner_ids, channel_ids, subtype_ids)