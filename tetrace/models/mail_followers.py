# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import re
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Followers(models.Model):
    _inherit = 'mail.followers'
    
    def _add_default_followers(self, res_model, res_ids, partner_ids, channel_ids=None, customer_ids=None):
        if self.env.context.get("add_follower"):
            return super(Followers, self)._add_default_followers(res_model, res_ids, partner_ids, channel_ids, customer_ids)
        return dict(), dict()
    
    def _add_followers(self, res_model, res_ids, partner_ids, partner_subtypes, channel_ids, channel_subtypes,
                       check_existing=False, existing_policy='skip'):
        if self.env.context.get("add_follower"):
            return super(Followers, self)._add_followers(res_model, res_ids, partner_ids, partner_subtypes, channel_ids, 
                                                         channel_subtypes, check_existing, existing_policy)
        return dict(), dict()
        