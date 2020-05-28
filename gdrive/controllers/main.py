# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GoogleDriveController(http.Controller):
    @http.route('/google_drive/authorize', type='http', auth='user', website=True)
    def authorize_google_drive(self, **kw):
        GoogleService = request.env['google.service'].sudo()
        GoogleDrive = request.env['google.gdrive'].sudo()

        context = kw.get('local_context', {})
        client_id = GoogleService.with_context(context).get_client_id('gdrive')

        from_url = '%s%s' % (request.env['ir.config_parameter'].sudo().get_param('web.base.url'), request.httprequest.path)
        url_authorize = GoogleDrive.with_context(context).authorize_google_uri(from_url=from_url)

        return request.render('gdrive.authorize', {
            'client_id': client_id,
            'url_authorize': url_authorize,
        })
