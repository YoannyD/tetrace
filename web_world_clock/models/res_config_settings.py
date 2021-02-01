# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import ast

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    clock_country_ids = fields.Many2many('res.country')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        set_param('clock_country_ids', self.clock_country_ids.ids)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        countries = get_param('clock_country_ids', default=[])
        clock_country_ids = ast.literal_eval(countries) if countries else []
        res.update(clock_country_ids=[(6, 0, clock_country_ids)])
        return res

    @api.model
    def horas_dashboard(self):
        _logger.warning("eeeee")
        return [{'name': "Canada"}]
