# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = "res.partner"

    siglas = fields.Char('Siglas')
    #cuenta_analitica_defecto_id se utiliza ser asignada a cada una de las lineas de una factura de compra CARGADA
    cuenta_analitica_defecto_id = fields.Many2one('account.analytic.account', string="Cuenta analitica por defecto", \
                                                  help="Cuenta analítica que tomarán las lineas de sus facturas cargadas", \
                                                  company_dependent=True)
    project_geo_ids = fields.One2many("project.project", "partner_geo_id")
    grupo_tetrace = fields.Boolean("Grupo Tetrace")
    project_ids = fields.Many2many("project.project")
    labels_type = fields.Many2many('res.company', string='Compañías')
    
    job_position_ids = fields.Many2many("res.partner.job_position", string="Puestos de trabajo")
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []

        if self.env.context.get("solo_company"):
            args = [('is_company', '=', True)]

        return super(Partner, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)
    
    def write(self, vals):
        res = super(Partner, self).write(vals)
        if not self.env.context.get('no_actualizar') and ('partner_latitude' in vals or 'partner_longitude' in vals):
            for r in self:
                r.project_geo_ids.write({
                    'partner_latitude': r.partner_latitude,
                    'partner_longitude': r.partner_longitude
                })
        return res
