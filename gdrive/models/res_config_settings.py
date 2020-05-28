# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import base64

from odoo import api, fields, models, modules

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_gdrive = fields.Boolean("Allow the users to synchronize with Google Drive")
    google_gdrive_client_id = fields.Char("Client_id")
    google_gdrive_client_secret = fields.Char("Client_key")
    google_gdrive_uri = fields.Char('URI for tuto')
    google_gdrive_carpeta = fields.Char('Carpeta', help="Carpeta donde se guardarán los archivos.")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        set_param('google_gdrive_client_id', (self.google_gdrive_client_id or '').strip())
        set_param('google_gdrive_client_secret', (self.google_gdrive_client_secret or '').strip())
        set_param('google_gdrive_carpeta', (self.google_gdrive_carpeta or '').strip())

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            google_gdrive_client_id=get_param('google_gdrive_client_id', default=''),
            google_gdrive_client_secret=get_param('google_gdrive_client_secret', default=''),
            google_gdrive_carpeta=get_param('google_gdrive_carpeta', default=''),
            google_gdrive_uri="%s/google_account/authentication" % get_param('web.base.url', default="http://yourcompany.odoo.com"),
        )
        return res
