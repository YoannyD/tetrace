# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http
from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class Invoice(http.Controller):
    @http.route(['/api/v1/analytic.line.rel'], type='http', auth='api_key')
    def listado_analytic_line_rel(self, offset=0, limit=10000, **kwargs):
        domain = []
        if limit: limit = int(limit)
        if offset: offset = int(offset)
        analytics = request.env['account.analytic.line.rel'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for analytic in analytics:
            data.append(self.get_values_account_analytic_line_rel(analytic))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_account_analytic_line_rel(self, analytic):
        values = {
            'id': analytic.id,
            'company_name': analytic.company_id.name,
            'date': analytic.date.strftime("%d/%m/%Y") if analytic.date else '',
            'account_id': analytic.account_id.name or '',
            'analytic_account_id': analytic.analytic_account_id.name or '',
            'currency_name': analytic.currency_id.name or '',
            'asiento_name': analytic.asiento_id.name or '',
            'debit': analytic.debit,
            'credit': analytic.credit,
        }
        
        return values
    
    @http.route(['/api/v1/account'], type='http', auth='api_key')
    def listado_account(self, offset=0, limit=10000, **kwargs):
        domain = []
        if limit: limit = int(limit)
        if offset: offset = int(offset)
        accounts = request.env['account.account'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for account in accounts:
            data.append(self.get_values_account(account))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_account(self, account):
        values = {
            'id': account.id,
            'name': account.name,
            'company_id': account.company_id.id or '',
            'company_name': account.company_id.name or '',
            'code': account.code or '',
        }
        return values
    
    @http.route(['/api/v1/analytic.account'], type='http', auth='api_key')
    def listado_analytic_account(self, offset=0, limit=10000, **kwargs):
        domain = []
        if limit: limit = int(limit)
        if offset: offset = int(offset)
        accounts = request.env['account.analytic.account'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for account in accounts:
            data.append(self.get_values_account_analytic(account))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_account_analytic(self, account):
        values = {
            'id': account.id,
            'name': account.name,
            'company_id': account.company_id.id or '',
            'company_name': account.company_id.name or '',
            'code': account.code or '',
        }
        return values
    
    @http.route(['/api/v1/company'], type='http', auth='api_key')
    def listado_company(self, offset=0, limit=10000, **kwargs):
        domain = []
        if limit: limit = int(limit)
        if offset: offset = int(offset)
        companies = request.env['res.company'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for company in companies:
            data.append(self.get_values_company(company))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_company(self, company):
        values = {
            'id': company.id,
            'name': company.name
        }
        return values
    
    