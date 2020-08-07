# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.addons.tetrace.models.conexion_mysql import ConexionMysql

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    _state_to = ["posted"]

    asiento_anticipo_id = fields.Many2one('account.move', domain=[('type', '=', 'entry')], string="Asiento anticipo")
    fecha_vencimiento_anticipo = fields.Date("Fecha vencimiento anticipo",
                                             compute="_compute_fecha_vencimiento_anticipo")
    incoterm_complemento = fields.Char('Complemento Incoterm')

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

            get_param = self.env['ir.config_parameter'].sudo().get_param
            try:
                journal_id = int(get_param('tetrace_account_move_jorunal_id', default=False))
            except:
                journal_id = False
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
