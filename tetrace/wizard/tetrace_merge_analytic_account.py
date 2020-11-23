# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from datetime import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MergeAnalyticAccount(models.TransientModel):
    _name = 'tetrace.merge_analytic_account'
    _description = 'Juntar líneas analíticas'
    
    analytic_account_id = fields.Many2one('tetrace.merge_analytic_account_line', string="Líneas analíticas")
    
    def action_merge_lines(self):
        self.ensure_one()
        if not self.analytic_account_id:
            raise ValidationError('Debe seleccionar una cuenta analítica.')

        lines = self.env['tetrace.merge_analytic_account_line'].search([])
        analytic_account_ids = [l.account_analytic_id.id for l in lines]
        
        companies = self.env['res.company'].search([])
        move_lines = self.env['account.move.line'].with_context(allowed_company_ids=companies.ids).search([
            ('move_id.state', 'in', ['posted', 'draft']),
            ('analytic_account_id', 'in', analytic_account_ids)
        ])
        
        for ml in move_lines:
            ml.write({'analytic_account_id': self.analytic_account_id.account_analytic_id.id})
            ml.analytic_line_ids.write({'account_id': self.analytic_account_id.account_analytic_id.id})

        return {'type': 'ir.actions.act_window_close'}
    
    def open_wizard(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }
    

class MergeAnalyticAccountLine(models.TransientModel):
    _name = 'tetrace.merge_analytic_account_line'
    _description = 'Líneas analíticas a junta'
    _rec_name = 'account_analytic_name'
    
    merge_analytic_account_ids = fields.One2many('tetrace.merge_analytic_account', 'analytic_account_id')
    account_analytic_id = fields.Many2one('account.analytic.account', string="Cuenta analítica", required=True)
    account_analytic_name = fields.Char(related="account_analytic_id.name")