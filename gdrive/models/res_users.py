# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class User(models.Model):

    _inherit = 'res.users'

    google_gdrive_rtoken = fields.Char('Refresh Token', copy=False)
    google_gdrive_token = fields.Char('User token', copy=False)
    google_gdrive_token_validity = fields.Datetime('Token Validity', copy=False)
    google_gdrive_last_sync_date = fields.Datetime('Last synchro date', copy=False)

    @api.multi
    def action_enviar_email_conexion_google_drive(self):
        template = self.env.ref('gdrive.email_conectar_con_google_drive', raise_if_not_found=False)

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.") % user.name)

            context = dict(
                self.env.context,
                lang=user.lang,
                base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            )
            template.with_context(context).send_mail(user.id, force_send=True, raise_exception=True)
            _logger.info("Envió de emails para conectarse a Google Drive a <%s> (<%s>)", user.login, user.email)
