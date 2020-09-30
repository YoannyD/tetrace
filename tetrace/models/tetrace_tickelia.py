# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class Tickelia(models.Model):
    _name = 'tetrace.tickelia'
    _description = 'Tickelia'

    name = fields.Char('Nombre')
    fecha = fields.Date('Fecha')
    company_id = fields.Many2one('res.company', required=True, default= lambda self: self.env.company)
    tickelia_trabajador_ids = fields.One2many('tetrace.tickelia.trabajador', 'tickelia_id')
    move_ids = fields.One2many('account.move', 'tickelia_id')

    def action_importar_tickelia(self):
        self.ensure_one()
        if self.move_ids:
            raise UserError("No se puede importar el fichero si existen asientos contables.")

        wizard = self.env['tetrace.importar_tickelia'].create({'tickelia_id': self.id})
        return wizard.open_wizard()

    def action_generar_asientos(self):
        for r in self:
            gastos_agrupados = {}
            for tickelia_trabajador in r.tickelia_trabajador_ids:
                key = tickelia_trabajador.liquidacion
                if key not in gastos_agrupados:
                    gastos_agrupados.update({key: []})
                gastos_agrupados[key].append(tickelia_trabajador)
    
            for key, gastos in gastos_agrupados.items():
                if not gastos:
                    continue      
                    
                ref = "Liquidación %s" % key
                date = gastos[0].fecha_liquidacion
                journal_id = self.env.company.tetrace_tickelia_journal_id.id
                if not journal_id:
                    raise ValidationError("Es necesario especificar un diario de liquidaciones de gato para la compañía")
                company_id = self.env.company.id

                values = {
                    'ref': ref,
                    'date': date,
                    'journal_id': journal_id,
                    'company_id': company_id,
                    'tickelia_id': self.id
                }

                gastos_ids = []
                line_ids = []
                for gasto in gastos:
                    name = gasto.descripcion
                    cuenta_gasto = gasto.cuenta_gasto
                    if not cuenta_gasto:
                        raise ValidationError(gasto.cuenta_gasto)

                    employee = gasto.employee_id
                    partner_id = employee.address_home_id.id if employee and employee.address_home_id else None
                    cuenta_analitica_id = gasto.cuenta_analitica_id
                    currency = gasto.currency_id

                    cuenta_contrapartida = gasto.cuenta_contrapartida
                    if not cuenta_contrapartida:
                        raise ValidationError(gasto.cuenta_gasto)

                    debit = gasto.importe
                    credit = gasto.importe

                    line_ids.append((0, 0, {
                        'name': name,
                        'account_id': cuenta_gasto.id if cuenta_gasto else None,
                        'partner_id': partner_id,
                        'analytic_account_id': cuenta_analitica_id.id if cuenta_analitica_id else None,
                        'debit': debit,
                        'credit': 0
                    }))

                    line_ids.append((0, 0, {
                        'name': name,
                        'account_id': cuenta_contrapartida.id if cuenta_contrapartida else None,
                        'partner_id': partner_id,
                        'debit': 0,
                        'credit': credit
                    }))

                    gastos_ids.append(gasto['id'])

                values.update({'line_ids': line_ids})
                self.env['account.move'].create(values)


class TickeliaTrabajador(models.Model):
    _name = 'tetrace.tickelia.trabajador'
    _description = 'Tickelia trabajadores'

    tickelia_id = fields.Many2one('tetrace.tickelia', string="Tickelia", required=True, ondelete="cascade")
    fecha= fields.Date('Fecha')
    company_id = fields.Many2one(related='tickelia_id.company_id')
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    cuenta_gasto = fields.Many2one('account.account')
    cuenta_contrapartida = fields.Many2one('account.account')
    descripcion = fields.Char('Descripción')
    importe = fields.Monetary('Importe validado')
    cuenta_analitica_id = fields.Many2one('account.analytic.account', string="Cuenta analítica")
    liquidacion = fields.Char('Liquidación')
    fecha_liquidacion = fields.Date('Fecha liquidación')
    currency_id = fields.Many2one(related='company_id.currency_id')
    incorrecta = fields.Boolean('Incorrecta', compute="_compute_incorrecta", store=True)

    @api.depends('fecha', 'importe', 'employee_id', 'cuenta_gasto', 'cuenta_contrapartida', 'cuenta_analitica_id')
    def _compute_incorrecta(self):
        for r in self:
            incorrecta = False
            if not r.fecha or not r.importe or not r.employee_id or not r.cuenta_gasto or not r.cuenta_contrapartida or not r.cuenta_analitica_id:
                incorrecta = True
            r.incorrecta = incorrecta
