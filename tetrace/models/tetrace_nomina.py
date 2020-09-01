# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Nomina(models.Model):
    _name = 'tetrace.nomina'
    _description = 'Nóminas'

    name = fields.Char('Nombre')
    fecha = fields.Date('Fecha')
    nomina_trabajador_ids = fields.One2many('tetrace.nomina.trabajador', 'nomina_id')
    move_ids = fields.One2many('account.move', 'nomina_id')

    def action_importar_nominas(self):
        self.ensure_one()
        wizard = self.env['tetrace.importar_nomina'].create({'nomina_id': self.id})
        return wizard.open_wizard()

    def action_generar_asientos(self):
        for r in self:
            agrupar_por_trabajador = {}
            for nomina_trabajador in r.nomina_trabajador_ids:
                key = '-1'
                if nomina_trabajador.employee_id and nomina_trabajador.employee_id.address_home_id:
                    key = str(nomina_trabajador.employee_id.address_home_id.id)

                if key not in agrupar_por_trabajador:
                    agrupar_por_trabajador.update({str(nomina_trabajador.employee_id): {
                        'nomina_id': r.id,
                        'date': nomina_trabajador.fecha_fin,
                        'journal_id': self.env.company.tetrace_nomina_jorunal_id.id,
                        'lines': []
                    }})

                partner_id = False
                if int(key) > 0:
                    partner_id = int(key)

                for analitica in nomina_trabajador.trabajador_analitica_ids:
                    debe = 0
                    haber = 0
                    if nomina_trabajador.debe > 0:
                        debe = analitica.importe
                    elif nomina_trabajador.haber > 0:
                        haber = analitica.importe

                    agrupar_por_trabajador[key]['lines'].append({
                        'account_id': r.account_id.id,
                        'partner_id': partner_id,
                        'name': r.descripcion,
                        'analytic_account_id': analitica.analytic_account_id.id,
                        'debit': debe,
                        'credit': haber
                    })


class NominaTrabajador(models.Model):
    _name = 'tetrace.nomina.trabajador'
    _description = 'Nóminas trabajadores'

    nomina_id = fields.Many2one('tetrace.nomina', string="Nómina", required=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')
    account_id = fields.Many2one('account.account')
    descripcion = fields.Char('Descripción')
    debe = fields.Monetary('Debe')
    haber = fields.Monetary('Haber')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    trabajador_analitica_ids = fields.One2many('tetrace.nomina.trabajador.analitica', 'nomina_trabajador_id')
    permitir_generar_analitica = fields.Boolean('Permitir generar distribución analítica', store=True,
                                                compute="_compute_permitir_generar_analitica")

    @api.depends('employee_id', 'account_id')
    def _compute_permitir_generar_analitica(self):
        for r in self:
            permitir = True
            if not r.employee_id or not r.account_id or (r.account_id and r.account_id.code[0] in ['6', '7']):
                permitir = False
            r.permitir_generar_analitica = permitir

    def mostrar_distribuciones_analiticas(self):
        self.ensure_one()
        view_form_id = self.env.ref('tetrace.tetrace_distribucion_analitica_trabajador_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [[view_form_id, 'form']],
            'target': 'new',
        }

    def _action_generar_distribucion_analitica(self):
        self.generar_distribucion_analitica()
        return self.mostrar_distribuciones_analiticas()

    def generar_distribucion_analitica(self):
        for r in self:
            if not r.permitir_generar_analitica:
                continue

            r.trabajador_analitica_ids.unlink()
            analiticas = self.env['account.analytic.line'].search([
                ('employee_id', '=', r.employee_id.id),
                ('date', '>=', r.fecha_inicio),
                ('date', '<=', r.fecha_fin),
            ], limit=1)

            total_horas = 0
            analitica_data = {}
            for analitica in analiticas:
                if not analitica.project_id or not analitica.project_id.analytic_account_id.id:
                    continue

                key = str(analitica.project_id.analytic_account_id.id)
                if key not in analitica_data:
                    analitica_data.update({key: {}})

                analitica_data[key].update({
                    'analytic_account_id': analitica.project_id.analytic_account_id.id,
                    'horas': analitica.unit_amount
                })
                total_horas += analitica.unit_amount

            importe_nomina = 0
            if r.debe > 0:
                importe_nomina = r.debe
            elif r.haber > 0:
                importe_nomina = r.haber

            for key, values in analitica_data.items():
                porcentaje = (values['horas'] * 100) / total_horas
                importe = (importe_nomina * 100) / porcentaje
                values.update({
                    'nomina_trabajador_id': r.id,
                    'porcentaje': porcentaje,
                    'importe': importe
                })

                self.env['tetrace.nomina.trabajador.analitica'].create(values)


class NominaTrabajadorAnalitica(models.Model):
    _name = 'tetrace.nomina.trabajador.analitica'
    _description = 'Dristribuciones analíticas nomina trabajador'

    nomina_trabajador_id = fields.Many2one('tetrace.nomina.trabajador', string="Nómina trabajador", required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta analítica")
    horas = fields.Float('Horas')
    employee_id = fields.Many2one(related="nomina_trabajador_id.employee_id")
    porcentaje = fields.Float('Porcentaje')
    importe = fields.Monetary('Importe')
    currency_id = fields.Many2one(related='nomina_trabajador_id.currency_id')
