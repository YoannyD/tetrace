# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_round

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
        if self.move_ids:
            raise UserError("No se puede importar el fichero si existen asientos contables.")

        wizard = self.env['tetrace.importar_nomina'].create({'nomina_id': self.id})
        return wizard.open_wizard()

    def action_generar_asientos(self):
        for r in self:
            agrupar_por_trabajador = {}
            for nomina_trabajador in r.nomina_trabajador_ids:
                if not nomina_trabajador.account_id:
                    continue

                key = '-1'
                if nomina_trabajador.employee_id and nomina_trabajador.employee_id.address_home_id:
                    key = str(nomina_trabajador.employee_id.address_home_id.id)

                if key not in agrupar_por_trabajador:
                    agrupar_por_trabajador.update({key: {
                        'nomina_id': r.id,
                        'ref' : "Nómina %s" % (nomina_trabajador.employee_id.name),
                        'date': nomina_trabajador.fecha_fin,
                        'journal_id': self.env.company.tetrace_nomina_journal_id.id,
                        'line_ids': []
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

                    agrupar_por_trabajador[key]['line_ids'].append((0, 0, {
                        'account_id': nomina_trabajador.account_id.id,
                        'partner_id': partner_id,
                        'name': nomina_trabajador.descripcion,
                        'analytic_account_id': analitica.analytic_account_id.id,
                        'debit': debe,
                        'credit': haber
                    }))

                if not nomina_trabajador.trabajador_analitica_ids:
                    agrupar_por_trabajador[key]['line_ids'].append((0, 0, {
                        'account_id': nomina_trabajador.account_id.id,
                        'partner_id': partner_id,
                        'name': nomina_trabajador.descripcion,
                        'debit': nomina_trabajador.debe,
                        'credit': nomina_trabajador.haber
                    }))

            for key, values in agrupar_por_trabajador.items():
                move = self.env['account.move'].search([
                    ('nomina_id', '=', values['nomina_id']),
                    ('ref', '=', values['ref']),
                    ('date', '=', values['date']),
                    ('journal_id', '=', values['journal_id'])
                ])
                if move:
                    if move.state == 'draft':
                        move.line_ids.unlink()
                        move.write(values)
                else:
                    self.env['account.move'].create(values)

    def action_generar_distribucion_analitica(self):
        for r in self:
            r.nomina_trabajador_ids.generar_distribucion_analitica()


class NominaTrabajador(models.Model):
    _name = 'tetrace.nomina.trabajador'
    _description = 'Nóminas trabajadores'

    nomina_id = fields.Many2one('tetrace.nomina', string="Nómina", required=True, ondelete="cascade")
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
    texto_importado = fields.Text('Texto importado')
    incorrecta_sin_distribucion = fields.Boolean('Incorrecta', compute="_compute_incorrecta_sin_distribucion", store=True)
    incorrecta_contrato_multiple = fields.Boolean('Incorrecta trabajador', compute="_compute_incorrecta_multiple_contrato", store=True)
    incorrecta_trabajador = fields.Boolean('Incorrecta trabajador', compute="_compute_incorrecta_trabajador", store=True)
    aviso_concepto_descuento = fields.Boolean('Aviso concepto descuento', compute="_compute_aviso_concepto_descuento", store=True)

    @api.depends('account_id', 'trabajador_analitica_ids')
    def _compute_incorrecta_sin_distribucion(self):
        for r in self:
            incorrecta_sin_distribucion = False
            if (r.account_id and r.account_id.code[0] in ['6', '7'] and not r.trabajador_analitica_ids):
                incorrecta_sin_distribucion = True
            r.incorrecta_sin_distribucion = incorrecta_sin_distribucion
    
    @api.depends('employee_id')
    def _compute_incorrecta_multiple_contrato(self):
        for r in self:
            incorrecta_contrato_multiple = False
            existe = self.env['tetrace.nomina.trabajador'].search_count([('nomina_id','=',r.nomina_id.id),('employee_id','=',r.employee_id.id), ('account_id','=',r.account_id.id)])
            if existe>1:
                incorrecta_contrato_multiple = True
            r.incorrecta_contrato_multiple = incorrecta_contrato_multiple
    
    @api.depends('employee_id')
    def _compute_incorrecta_trabajador(self):
        for r in self:
            incorrecta_trabajador = False
            if not r.employee_id:
                incorrecta_trabajador = True
            r.incorrecta_trabajador = incorrecta_trabajador
    
    @api.depends('account_id','haber')
    def _compute_aviso_concepto_descuento(self):
        for r in self:
            aviso_concepto_descuento = False
            if r.account_id and r.account_id.code[0] in ['7'] and r.haber>0:
                aviso_concepto_descuento = True
            r.aviso_concepto_descuento = aviso_concepto_descuento
            
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for r in self:
            r.generar_distribucion_analitica()

    @api.depends('employee_id', 'account_id')
    def _compute_permitir_generar_analitica(self):
        for r in self:
            permitir = False
            if r.employee_id and r.account_id and r.account_id.code[0] in ['6', '7']:
                permitir = True
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

    def action_generar_distribucion_analitica(self):
        self.generar_distribucion_analitica()
        return self.mostrar_distribuciones_analiticas()

    def generar_distribucion_analitica(self):
        for r in self:
            if not r.permitir_generar_analitica:
                continue

            r.trabajador_analitica_ids.unlink()
            analiticas = self.env['account.analytic.line'].sudo().search([
                ('employee_id', '=', r.employee_id.id),
                ('date', '>=', r.fecha_inicio),
                ('date', '<=', r.fecha_fin),
                '|', ('company_id', '=', False), ('company_id', 'in', self.env.user.company_ids.ids)
            ])

            total_horas = 0
            analitica_data = {}
            for analitica in analiticas:
                if not analitica.project_id or not analitica.project_id.analytic_account_id.id:
                    continue

                key = str(analitica.project_id.analytic_account_id.id)
                if key not in analitica_data:
                    analitica_data.update({
                        key: {
                            'analytic_account_id': analitica.project_id.analytic_account_id.id,
                            'horas': 0
                        }
                    })

                analitica_data[key]['horas'] += analitica.unit_amount
                total_horas += analitica.unit_amount

            importe_nomina = 0
            if r.debe > 0:
                importe_nomina = r.debe
            elif r.haber > 0:
                importe_nomina = r.haber

            importe_total = 0
            for key, values in analitica_data.items():
                porcentaje = (values['horas'] * 100) / total_horas
                importe = "%.2f" % ((importe_nomina * porcentaje) / 100)
                if float(importe) <= 0:
                    continue

                importe_total += float(importe)
                values.update({
                    'nomina_trabajador_id': r.id,
                    'porcentaje': porcentaje,
                    'importe': importe
                })

                self.env['tetrace.nomina.trabajador.analitica'].create(values)

            if importe_total and importe_nomina != importe_total:
                analitica = self.env['tetrace.nomina.trabajador.analitica'].search([
                    ('nomina_trabajador_id', '=', r.id)
                ], order="importe desc", limit=1)
                if importe_nomina > importe_total:
                    dif = importe_total - importe_nomina
                    analitica.write({'importe': analitica['importe'] - dif})
                else:
                    dif = importe_nomina - importe_total
                    analitica.write({'importe': analitica['importe'] + dif})


class NominaTrabajadorAnalitica(models.Model):
    _name = 'tetrace.nomina.trabajador.analitica'
    _description = 'Dristribuciones analíticas nomina trabajador'

    nomina_trabajador_id = fields.Many2one('tetrace.nomina.trabajador', string="Nómina trabajador", required=True,
                                           ondelete="cascade")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta analítica")
    horas = fields.Float('Horas')
    employee_id = fields.Many2one(related="nomina_trabajador_id.employee_id")
    porcentaje = fields.Float('Porcentaje')
    importe = fields.Monetary('Importe')
    currency_id = fields.Many2one(related='nomina_trabajador_id.currency_id')
