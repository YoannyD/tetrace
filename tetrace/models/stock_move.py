# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_show_details(self):
        self.ensure_one()
        res = super(StockMove, self).action_show_details()
        res['context'].update({'default_location_dest_id': False})
        return res
