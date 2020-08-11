# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AssetModify(models.TransientModel):
    _inherit = 'asset.modify'

    @api.model
    def create(self, vals):
        if 'asset_id' in vals:
            asset = self.env['account.asset'].browse(vals['asset_id'])

            if 'account_depreciation_expense_id' not in vals:
                vals.update({'account_depreciation_expense_id': asset.analytic_account_id.id})

        return super(AssetModify, self).create(vals)
