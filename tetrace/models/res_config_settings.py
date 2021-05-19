# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    auto_add_followers = fields.Boolean('Auto añadir seguidores', default=False)
    dia_bloqueo = fields.Integer('Días de bloqueo registro de horas mes anterior', default=5)
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        auto_add_followers = True if self.auto_add_followers else False
        set_param('auto_add_followers', auto_add_followers)
        try:
            dia_bloqueo = int(self.dia_bloqueo)
        except:
            dia_bloqueo = 5
        set_param('dia_bloqueo', dia_bloqueo)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(auto_add_followers=get_param('auto_add_followers', default=False))
        try:
            dia_bloqueo = int(get_param('dia_bloqueo', default=5))
        except:
            dia_bloqueo = 5
        res.update(dia_bloqueo=dia_bloqueo)
        return res