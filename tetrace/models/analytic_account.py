# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    _description = 'Analytic Account'
    
    estructurales = fields.Boolean(string='Estructurales', default=False)
    update_from_sale_order = fields.Boolean("Actualizar desde Pedido de Venta", default=True)
    sale_order_ids = fields.One2many("sale.order", "analytic_account_id")
    sale_order_count = fields.Integer("Nº Pedidos de venta", store=True,
                                      compute="_compute_sale_order")
    analitica_cerrada = fields.Boolean("Cuenta analítica cerrada")
#     horas_laborables = fields.Float("Horas laborables",)

    @api.depends("sale_order_ids")
    def _compute_sale_order(self):
        for r in self:
            r.sale_order_count = len(r.sale_order_ids)
    
    @api.constrains('company_id')
    def _check_company_id(self):
        for record in self:
            _logger.warning("Anulamos?")

            
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    line_rel_ids = fields.One2many('account.analytic.line.rel', 'analytic_line_id')

    def _timesheet_preprocess(self, vals):
        #Modificamos el comportamiento anterior mediante el cual si la cuenta analitica asociada a la proyecto
        #no tenia indicada la compañia entonces saltaba un error; ahora si no hay compañia se toma la del entorno
        #de esta manera permitimos que podamos compartir esa cuenta analitica entre las distintas compañías
        vals = super(AccountAnalyticLine, self)._timesheet_preprocess(vals)

        if vals.get('project_id'):
            project = self.env['project.project'].browse(vals.get('project_id'))
            if project:
                vals['company_id'] = project.company_id.id
                vals['product_uom_id'] = project.company_id.project_time_mode_id.id

        return vals

    @api.model_create_multi
    def create(self, vals):
        lines = super(AccountAnalyticLine, self).create(vals)
        for line in lines:
            line._check_imputar_tiempos()
            self.env['account.analytic.line.rel'].create({'analytic_line_id': line.id})
        return lines
                
    def write(self, vals):
        self._check_imputar_tiempos()
        return super(AccountAnalyticLine, self).write(vals)

    def unlink(self):
        for line in self:
            line.line_rel_ids.unlink()
        res = super(AccountAnalyticLine, self).unlink()
        return res

    def _check_imputar_tiempos(self):
        for r in self:
            if r.task_id:
                if r.task_id.stage_id and r.task_id.stage_id.bloquear_imputar_tiempos:
                    raise ValidationError(_("La inserción de tiempos en la tarea esta bloqueda."))
                
                if not r.date or (self.env.company.fecha_bloque_imputacion_horas and 
                                  r.date < self.env.company.fecha_bloque_imputacion_horas):
                    raise ValidationError(_("Está intentando añadir un registro en un periodo ya cerrado."))


class AccountAnalyticLineRel(models.Model):
    _name = 'account.analytic.line.rel'
    _description = 'Líneas analítica (relación)'

    analytic_line_id = fields.Many2one('account.analytic.line', string="Línea analítica", required=True,
                                       ondelete='cascade')
    asiento_id = fields.Many2one(related="analytic_line_id.move_id.move_id", string="Asiento contable")
    debit = fields.Monetary('Debit', compute="_compute_debit_credit", store=True)
    credit = fields.Monetary('Credit', compute="_compute_debit_credit", store=True)
    account_id = fields.Many2one(related="analytic_line_id.general_account_id", store=True)
    currency_id = fields.Many2one(related="analytic_line_id.currency_id", store=True)
    date = fields.Date(related="analytic_line_id.date", store=True)
    company_id = fields.Many2one(related="analytic_line_id.company_id", store=True)
    balance = fields.Monetary('Balance', compute="_compute_debit_credit", store=True)
    analytic_account_id = fields.Many2one(related="analytic_line_id.account_id", store=True)
    estructurales = fields.Boolean(related="analytic_line_id.account_id.estructurales", store=True)
    importe_euro = fields.Float("Importe EUR", compute="_compute_debit_credit", store=True)

    @api.depends('analytic_line_id', 'analytic_line_id.amount')
    def _compute_debit_credit(self):
        for r in self:
            credit = 0
            debit = 0
            amount = r.analytic_line_id.amount
            if amount > 0:
                credit = amount
            else:
                debit = -amount

            company = self.env['res.company'].browse(1)
            cr = r.currency_id._get_rates(company, r.date)
            rate = 1.0
            for key, value in cr.items():
                rate = value
                break

            importe_euro = abs(r.analytic_line_id.amount) * rate
                
            r.update({
                'credit': credit,
                'debit': debit,
                'balance': debit - credit,
                'importe_euro': importe_euro
            })
