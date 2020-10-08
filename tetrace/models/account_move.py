# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.addons.tetrace.models.conexion_mysql import ConexionMysql

_logger = logging.getLogger(__name__)

CODIGOS_SII = [
    ('33', 'Factura electrónica'),
    ('34', 'Factura no afecta o exenta electrónica'),
    ('56', 'Nota de débito electrónica'),
    ('61', 'Nota de crédito electrónica')
]


class AccountMove(models.Model):
    _inherit = "account.move"
    _state_to = ["posted"]

    def _default_validacion_id(self):
        validacion = self.env['tetrace.validacion_user'].search([
            ('user_id', '=', self.env.user.id),
            ('validacion_id', '!=', False)
        ], limit=1)
        if validacion:
            return validacion.id
        return None

    asiento_anticipo_id = fields.Many2one('account.move', domain=[('type', '=', 'entry')], string="Asiento anticipo")
    fecha_vencimiento_anticipo = fields.Date("Fecha vencimiento anticipo",
                                             compute="_compute_fecha_vencimiento_anticipo")
    incoterm_complemento = fields.Char('Complemento Incoterm')
    secuencia_num = fields.Integer('Número secuencia')
    secuencia = fields.Char('Secuencia')
    nomina_id = fields.Many2one('tetrace.nomina', string="Nómina")
    validacion_id = fields.Many2one('tetrace.validacion_user', string="Validación",
                                    default=lambda self: self._default_validacion_id())
    tickelia_id = fields.Many2one('tetrace.tickelia', string="Tickelia")
    codigo_sii = fields.Selection(CODIGOS_SII, string="Código SII")
    fecha_servicio = fields.Date("Fecha servicio")

    @api.onchange('ref')
    def _onchange_ref_invoice(self):
        for r in self:
            if r.journal_id.type == 'purchase':
                r.invoice_payment_ref = r.ref 
                
    def _compute_fecha_vencimiento_anticipo(self):
        for r in self:
            fecha_vencimiento_anticipo = None
            if r.asiento_anticipo_id:
                for line in r.asiento_anticipo_id.line_ids:
                    if line.date_maturity and line.account_id and line.account_id.group_id and \
                        line.account_id.group_id.code_prefix == '5200':
                        fecha_vencimiento_anticipo = line.date_maturity
                        break
            r.fecha_vencimiento_anticipo = fecha_vencimiento_anticipo

    @api.onchange('invoice_date')
    def _onchange_fecha_servicio(self):
        for r in self:
            if r.type == 'out_invoice' and r.invoice_date:
                fecha_servicio_primer_dia_mes = r.invoice_date.replace(day=1)
                fecha_servicio_ultimo_dia_mes_anterior = fecha_servicio_primer_dia_mes - timedelta(days=1)
                r.fecha_servicio = fecha_servicio_ultimo_dia_mes_anterior

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)

        if res.journal_id.type == 'sale':
            secuencia, name = res.generar_secuencia()
            res.write({
                'secuencia_num': secuencia,
                'secuencia': name
            })
        return res

    def generar_secuencia(self):
        self.ensure_one()
        secuencia_num = 1
        move = self.search([
            ('journal_id.type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
            ('secuencia_num', '!=', False)
        ], limit=1, order="secuencia_num desc")

        if move:
            secuencia_num = move.secuencia_num + 1

        numero_faltantes = 4 - len(str(secuencia_num))
        numero_completo = str(secuencia_num)
        for n in range(numero_faltantes):
            numero_completo = "0%s" % numero_completo

        name = "PROF/%s/%s" % (datetime.now().year, numero_completo)
        return secuencia_num, name

    @api.model
    def importar_gastos_tickelia(self):
        cnx = ConexionMysql()
        query = "SELECT * FROM Tickelia_2 where TraspasoOdoo = 0 and Cuenta_Contable != ''"
        data = cnx.execute(query)

        gastos_agrupados = {}
        for r in data:
            key = "%s-%s" % (r[u'id_Liquidaci\xf3n'], r['Tique_Factura'])
            if key not in gastos_agrupados:
                gastos_agrupados.update({key: []})
            gastos_agrupados[key].append(r)

        for key, gastos in gastos_agrupados.items():
            if not gastos:
                continue

            ref = "Liquidación %s" % gastos[0][u'id_Liquidaci\xf3n']
            date = None
            if gastos[0][u'Fecha_Liquidaci\xf3n']:
                fecha_aux = gastos[0][u'Fecha_Liquidaci\xf3n'].split(" ")[0]
                date = datetime.strptime(fecha_aux, "%d/%m/%Y").strftime("%Y-%m-%d")

            journal_id = False
            if self.env.company.tetrace_tickelia_journal_id:
                journal_id = self.env.company.tetrace_tickelia_journal_id.id

            company = self.env['res.company'].search([('vat', '=', "ES%s" % gastos[0]['NIF_Empresa'])], limit=1)

            values = {
                'ref': ref,
                'date': date,
                'journal_id': journal_id,
                'company_id': company.id if company else None,
            }

            gastos_ids = []
            line_ids = []
            for gasto in gastos:
                name = "%s%s" % (gasto['Tipo Gasto'], gasto['SubTipo_Gasto'])

                account_1 = self.env['account.account'].search([
                    ('code', '=', gasto['Cuenta_Contable']),
                    ('company_id', '=', company.id)
                ], limit=1)

                if not account_1:
                    raise ValidationError(gasto['Cuenta_Contable'])

                employee = self.env['hr.employee'].sudo().search([('identification_id', '=', gasto['DNI_Usuario'])],
                                                                 limit=1)
                partner_id = employee.address_home_id.id if employee and employee.address_home_id else None

                analytic_buscar = "46%s" % gasto['id_Proyecto']
                analytic = self.env['account.analytic.account'].search([('code', '=like', analytic_buscar)], limit=1)
                if not analytic:
                    analytic = self.env['account.analytic.account'].create({
                        'name': analytic_buscar,
                        'code': analytic_buscar
                    })

                currency = self.env['res.currency'].search([('name', '=', gasto['Moneda_Base'])], limit=1)

                cuenta_a_buscar = gasto['Cuenta_Contable_Tarjeta']
                if not cuenta_a_buscar:
                    cuenta_a_buscar = gasto['Cuenta_Contable_Anticipos']

                account_2 = self.env['account.account'].search([
                    ('code', '=', cuenta_a_buscar),
                    ('company_id', '=', company.id)
                ], limit=1)

                if not account_2:
                    continue
                #                     raise ValidationError(cuenta_a_buscar)

                debit = gasto['Importe_Base_Validado'].replace(",", ".")
                credit = gasto['Importe_Base_Validado'].replace(",", ".")

                line_ids.append((0, 0, {
                    'name': name,
                    'account_id': account_1.id if account_1 else None,
                    'partner_id': partner_id,
                    'analytic_account_id': analytic.id if analytic else None,
                    #                     'currency_id': currency.id if currency else None,
                    'debit': debit,
                    'credit': 0
                }))

                line_ids.append((0, 0, {
                    'name': name,
                    'account_id': account_2.id if account_2 else None,
                    'partner_id': partner_id,
                    #'analytic_account_id': analytic.id if analytic else None,
                    #                     'currency_id': currency.id if currency else None,
                    'debit': 0,
                    'credit': credit
                }))

                gastos_ids.append(gasto['id'])

            values.update({'line_ids': line_ids})
            self.create(values)

class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"
    
    @api.model
    def create_exchange_rate_entry(self, aml_to_fix, move):
        # Añadir al asiento de diferencia de cambio generado automaticamente
        # la cuenta analitica establecida en los parametros de la compañía
        res = super(AccountPartialReconcile, self).create_exchange_rate_entry(aml_to_fix, move)  
        for apunte in move.line_ids:
            # Si el tipo de cuenta del apunte es:
            # 13: Ingreso
            # 15: Gastos
            # Indicamos la cuenta analitica establecida en la compañía para estos casos
            if apunte.account_id.user_type_id.id == 13 or apunte.account_id.user_type_id.id ==15:
                apunte.write({'analytic_account_id' : apunte.company_id.tetrace_cuenta_analitica_diferencia_cambio.id})
        return res