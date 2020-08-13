# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = "res.company"

    tetrace_account_move_jorunal_id = fields.Many2one('account.journal', string='Diario de liquidaciones')
