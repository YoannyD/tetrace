# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Validacion(models.Model):
    _name = 'tetrace.validacion'
    _description = "Validaciones"

    name = fields.Char('Nombre', required=True, translate=True)
    validacion_user_ids = fields.One2many('tetrace.validacion_user', 'validacion_id')

    _sql_constraints = [
        ("name_unique", "unique(name)", _("Ya existe una valoración con ese nombre"))
    ]


class ValidacionUser(models.Model):
    _name = 'tetrace.validacion_user'
    _description = "Validaciones usuario"
    _order = "sequence,id"

    sequence = fields.Integer('Secuencia')
    name = fields.Char('Nombre', compute="_compute_name", store=True)
    validacion_id = fields.Many2one('tetrace.validacion', string="Validación")
    user_id = fields.Many2one('res.users', string="Usuario")

    @api.depends('validacion_id.name', 'user_id.name')
    def _compute_name(self):
        for r in self:
            r.name = "%s [%s]" % (r.validacion_id.name, r.user_id.name)
