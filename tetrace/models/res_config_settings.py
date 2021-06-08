# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    auto_add_followers = fields.Boolean('Auto añadir seguidores', default=False)
    template_act_project_id = fields.Many2one('project.project', string="Plantilla proyecto activación")
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        auto_add_followers = True if self.auto_add_followers else False
        set_param('auto_add_followers', auto_add_followers)
        
        try:
            template_act_project_id = int(self.template_act_project_id.id)
        except:
            template_act_project_id = None
        
        set_param('template_act_project_id', template_act_project_id)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(auto_add_followers=get_param('auto_add_followers', default=False))
        
        try:
            template_act_project_id = int(get_param('template_act_project_id'))
        except:
            template_act_project_id = None
        
        res.update(template_act_project_id=template_act_project_id)
        return res