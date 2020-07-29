# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    debit = fields.Monetary('Debit', compute="_compute_debit_credit", store=True)
    credit = fields.Monetary('Credit', compute="_compute_debit_credit", store=True)
    account_id = fields.Many2one('account.account', 'Cuenta financiera', required=True, ondelete='restrict',
                                 index=True, compute="_compute_general_account_id", store=True)

    @api.depends('amount')
    def _compute_debit_credit(self):
        for r in self:
            credit = 0
            debit = 0
            if r.amount > 0:
                credit = r.amount
            else:
                debit = r.amount

            r.update({
                'credit': credit,
                'debit': debit,
            })

    @api.depends('general_account_id')
    def _compute_general_account_id(self):
        for r in self:
            r.account_id = r.general_account_id.id if r.general_account_id else None
