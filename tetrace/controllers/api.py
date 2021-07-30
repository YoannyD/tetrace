# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http
from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class TetraceAPI(http.Controller):
    @http.route(['/api/v1/company'], type='http', auth='api_key')
    def listado_company(self, offset=0, limit=1000000, **kwargs):
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
    
    @http.route(['/api/v1/account'], type='http', auth='api_key')
    def listado_account(self, offset=0, limit=1000000, **kwargs):
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
            'company_id': account.company_id.id or '',
            'company_name': account.company_id.name or '',
            'name': account.name,
            'code': account.code or '',
            'cuenta_consolidacion' : account.tetrace_account_id.name,
        }
        return values  
    
    @http.route(['/api/v1/account.bank.statement'], type='http', auth='api_key')
    def listado_bank_statement(self, fecha_desde=None, offset=0, limit=1000000, **kwargs):
        domain=[]
        if fecha_desde: domain += [('date','>=', fecha_desde)] 
        if limit: limit = int(limit)     
        if offset: offset = int(offset)        
            
        lines = request.env['account.bank.statement'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for line in lines:
            data.append(self.get_values_bank_statement(line))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_bank_statement(self, line):
        values = {
            'id': line.id,
            'company_id': line.company_id.id or '',
            'company_name': line.company_id.name or '',
            'fecha': line.date.strftime("%d/%m/%Y") if line.date else '',
            'diario': line.journal_id.name  or '',
            'moneda': line.currency_id.name or '',
            'referencia': line.name or '/',
            'saldo_inicial': line.balance_start or 0,
            'saldo_final': line.balance_end_real or 0,
        }
        
        return values   
    @http.route(['/api/v1/account.bank.statement.line'], type='http', auth='api_key')
    def listado_bank_statement_line(self, fecha_desde=None, offset=0, limit=1000000, **kwargs):
        domain=[]
        if fecha_desde: domain += [('date','>=', fecha_desde)] 
        if limit: limit = int(limit)     
        if offset: offset = int(offset)        
            
        lines = request.env['account.bank.statement.line'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for line in lines:
            data.append(self.get_values_bank_statement_line(line))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_bank_statement_line(self, line):
        values = {
            'id': line.id,
            'company_id': line.company_id.id or '',
            'company_name': line.company_id.name or '',
            'fecha': line.date.strftime("%d/%m/%Y") if line.date else '',
            'diario': line.journal_id.name  or '',
            'diario_moneda': line.journal_currency_id.name  or '',
            'extracto': line.statement_id.name or '',
            'referencia': line.ref or '/',
            'etiqueta': line.name or '',
            'empresa': line.partner_id.name or '',
            'importe': line.amount or 0,
            'moneda' : line.currency_id.name,
            'importe_moneda': line.amount_currency or 0,
        }
        
        return values    

    @http.route(['/api/v1/account.move.line'], type='http', auth='api_key')
    def listado_account_move_line(self, fecha_desde=None, offset=0, limit=1000000, **kwargs):
        domain=[('parent_state','=','posted')]
        if fecha_desde: domain += [('date','>=', fecha_desde)] 
        if limit: limit = int(limit) 
        if offset: offset = int(offset)
            
        lines = request.env['account.move.line'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for line in lines:
            data.append(self.get_values_account_move_line(line))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_account_move_line(self, line):
        values = {
            'id': line.id,
            'company_id': line.company_id.id or '',
            'company_name': line.company_id.name or '',
            'company_currency' : line.company_currency_id.name,
            'fecha': line.date.strftime("%d/%m/%Y") if line.date else '',
            'asiento_contable': line.move_id.name or '', 
            'diario': line.journal_id.name  or '',
            'cuenta': line.account_id.code  or '',
            'cuenta_consolidacion': line.tetrace_account_id.name  or '',
            'empresa': line.partner_id.name  or '',
            'etiqueta': line.name or '',
            'referencia': line.ref or '',
            'debe': line.debit or 0,
            'haber': line.credit or 0,
            'importe' : line.balance or 0,
            'importe_residual': line.amount_residual or 0,
            'moneda' : line.currency_id.name,
            'importe_moneda': line.amount_currency or 0,
            'importe_residual_moneda': line.amount_residual_currency or 0,
            'fecha_vencimiento': line.date_maturity.strftime("%d/%m/%Y") if line.date_maturity else '',
            'reconciliado' : line.reconciled,
            'asiento_conciliacion': line.full_reconcile_id.name  or '',         
            'cuenta_analitica': line.analytic_account_id.name  or '',
            'etiqueta_analitica': [l.name for l in line.analytic_tag_ids],
            'asiento_anticipo_id': line.asiento_anticipo_id.name or '',
            'confirmado': line.confirmado,
        }
        
        return values
    
    @http.route(['/api/v1/analytic.account'], type='http', auth='api_key')
    def listado_analytic_account(self, offset=0, limit=1000000, **kwargs):
        domain = []
        if limit: limit = int(limit)
        if offset: offset = int(offset)
        analytics = request.env['account.analytic.account'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for analytic in analytics:
            data.append(self.get_values_analytic_account(analytic))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_analytic_account(self, analytic):
        values = {
            'id': analytic.id,
            'company_id': analytic.company_id.id or '',
            'company_name': analytic.company_id.name or '',
            'name': analytic.name,
            'code': analytic.code or '',
        }
        return values    
    
    @http.route(['/api/v1/analytic.line.rel'], type='http', auth='api_key')
    def listado_analytic_line_rel(self, fecha_desde=None, offset=0, limit=1000000, **kwargs):
        domain = []
        if fecha_desde: domain += [('date','>=', fecha_desde)] 
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
            'company_id': analytic.company_id.id or '',
            'company_name': analytic.company_id.name,
            'fecha': analytic.date.strftime("%d/%m/%Y") if analytic.date else '',
            'cuenta': analytic.account_id.code  or '',
            'cuenta_consolidacion': analytic.account_id.tetrace_account_id.name  or '',
            'codigo_cuenta_consolidacion': analytic.account_id.tetrace_account_id.code  or '',
            'cuenta_analitica': analytic.analytic_account_id.name  or '',
            'estructurales': analytic.estructurales,
            'moneda' : analytic.currency_id.name,
            'asiento_contable': analytic.asiento_id.name or '', 
            'debe': analytic.debit,
            'haber': analytic.credit,
            'balance': analytic.balance,
            'moneda' : analytic.currency_id.name,
        }
        
        return values
    
    

    
    