# Copyright 2018 Giacomo Grasso <giacomo.grasso.82@gmail.com>
# Odoo Proprietary License v1.0 see LICENSE file

from odoo import models, fields, api, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    treasury_planning = fields.Boolean(
        string="Treasury Planning",
        company_dependent=True)


class AccountMove(models.Model):
    """Account move have type depending on their journal for domain purposes"""
    _inherit = "account.move"

    journal_type = fields.Selection(related="journal_id.type", string="Journal Type")
    date_treasury = fields.Date(string="Treasury Date")

    @api.onchange('invoice_date')
    def onchange_invoice_date(self):
        if self.invoice_date:
            self.date_treasury = self.invoice_date
        else:
            self.date_treasury = False


class AccountMoveLine(models.Model):
    """Move lines are now linked to a treasury forecast depending on the
       treasury date, and thei inherit thei cash flow share 1) from invoice
       or 2) from their account move structure"""
    _inherit = "account.move.line"

    treasury_date = fields.Date(string='Treas. Date')
    forecast_id = fields.Many2one(
        comodel_name='treasury.forecast',
        compute='_compute_treasury_forecast',
        store=True,
        string='Forecast')
    treasury_planning = fields.Boolean(
        compute='_compute_forecast_planning',
        store=True,
        string='FP')
    bank_statement_line_id = fields.Many2one(
        comodel_name='account.bank.statement.line',
        string='Bank statement line',
        store=True)

    @api.depends('account_id.treasury_planning')
    def _compute_forecast_planning(self):
        for account in self:
            account.treasury_planning = account.account_id.treasury_planning

    @api.model_create_multi
    def create(self, vals):
        """At move line creation the treasury date is equal to the due date"""
        item = super().create(vals)
        for line in item:
            line.treasury_date = line.date_maturity
        return item

    @api.depends('treasury_date')
    def _compute_treasury_forecast(self):
        """Move line is associated to the treasury forecast
           depending on the treasury date"""
        for item in self:
            if item.treasury_date and item.treasury_planning:
                forecast_obj = self.env['treasury.forecast']
                forecast_id = forecast_obj.search([
                    ('date_start', '<=', item.treasury_date),
                    ('date_end', '>=', item.treasury_date),
                    ('state', '=', 'open')])
                if forecast_id:
                    item.forecast_id = forecast_id[0].id
                else:
                    item.forecast_id = False
            else:
                item.forecast_id = False

    def set_treasury_date(self):
        for line in self:
            line.treasury_date = line.date_maturity


class AccountJournal(models.Model):
    _inherit = "account.journal"

    treasury_planning = fields.Boolean(string="Treasury Planning")
