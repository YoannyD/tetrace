# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tetrace_account_move_jorunal_id = fields.Many2one('account.journal', string='Diario de liquidaciones')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        tetrace_account_move_jorunal_id = False
        if self.tetrace_account_move_jorunal_id:
            tetrace_account_move_jorunal_id = self.tetrace_account_move_jorunal_id.id
        set_param('tetrace_account_move_jorunal_id', tetrace_account_move_jorunal_id)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param

        try:
            tetrace_account_move_jorunal_id = int(get_param('tetrace_account_move_jorunal_id', default=False))
        except:
            tetrace_account_move_jorunal_id = False
        res.update(tetrace_account_move_jorunal_id=tetrace_account_move_jorunal_id)
        return res
