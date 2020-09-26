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
            continue


class TickeliaTrabajador(models.Model):
    _name = 'tetrace.tickelia.trabajador'
    _description = 'Tickelia trabajadores'

    tickelia_id = fields.Many2one('tetrace.tickelia', string="Tickelia", required=True, ondelete="cascade")
    fecha= fields.Date('Fecha')
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    cuenta_gasto = fields.Many2one('account.account')
    cuenta_contrapartida = fields.Many2one('account.account')
    descripcion = fields.Char('Descripción')
    importe = fields.Monetary('Importe validado')
    cuenta_analitica_id = fields.Many2one('account.analytic.account', string="Cuenta analítica")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    incorrecta = fields.Boolean('Incorrecta', compute="_compute_incorrecta", store=True)

    @api.depends('fecha', 'importe', 'employee_id', 'cuenta_gasto', 'cuenta_contrapartida', 'cuenta_analitica_id')
    def _compute_incorrecta(self):
        for r in self:
            incorrecta = False
            if not r.fecha or not r.importe or not r.employee_id or not r.cuenta_gasto or not r.cuenta_contrapartida or not r.cuenta_analitica_id:
                incorrecta = True
            r.incorrecta = incorrecta
