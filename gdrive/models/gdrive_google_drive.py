# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import logging
import json
import base64

from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)


def status_response(status):
    return int(str(status)[0]) == 2


class GoogleDrive(models.AbstractModel):
    STR_SERVICE = 'gdrive'
    _name = 'google.%s' % STR_SERVICE

    MSG_ERROR_USER = 'El contacto no tiene ligado un usuario.'
    HEADERS_REQUEST = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    BASE_URL_DRIVE = '/drive/v3'

    def obtener(self, field_id, params_query=None, user=None):
        url = "%s/files/%s?access_token=%s" % (self.BASE_URL_DRIVE, field_id, self.get_token(user))
        url += params_query if params_query else ''
        return self.env['google.service']._do_request(url, {}, self.HEADERS_REQUEST, type='GET')

    def buscar(self, params_query=None, user=None):
        url = "%s/files?access_token=%s" % (self.BASE_URL_DRIVE, self.get_token(user))
        url += params_query if params_query else ''
        return self.env['google.service']._do_request(url, {}, self.HEADERS_REQUEST, type='GET')

    def export(self, field_id, params_query=None, user=None):
        url = "%s/files/%s/export?access_token=%s" % (self.BASE_URL_DRIVE, field_id, self.get_token(user))
        url += params_query if params_query else ''
        return self.env['google.service']._do_request(url, {}, self.HEADERS_REQUEST, type='GET')

    def crear(self, data=None, params_query=None, user=None):
        if not data:
            data = {}
        url = "%s/files?access_token=%s" % (self.BASE_URL_DRIVE, self.get_token(user))
        url += params_query if params_query else ''
        return self.env['google.service']._do_request(url, json.dumps(data), self.HEADERS_REQUEST, type='POST')

    def subir_archivo(self, fichero, data=None, params_query=None, user=None):
        if not data:
            data = {}

        url = "%s/files?access_token=%s" % ('/upload/drive/v3', self.get_token(user))
        url += params_query if params_query else ''

        boundary = '-------314159265358979323846'
        delimiter = "\r\n--%s\r\n" % boundary
        close_delim = "\r\n--%s--" % boundary
        mimetype = guess_mimetype(base64.b64decode(fichero))
        multipartRequestBody = '%sContent-Type: application/json\r\n\r\n%s%sContent-Type: %s \r\nContent-Transfer-Encoding: base64\r\n\r\n%s%s' % \
                               (delimiter, json.dumps(data), delimiter, mimetype, fichero, close_delim)

        headers_request = {'content-type': 'multipart/related; boundary=%s' % boundary }
        return self.env['google.service']._do_request(url, multipartRequestBody, headers_request, type='POST')

    def copiar(self, file_id, data=None, params_query=None, user=None):
        if not data:
            data = {}
        url = "%s/files/%s/copy?access_token=%s" % (self.BASE_URL_DRIVE, file_id, self.get_token(user))
        url += params_query if params_query else ''
        return self.env['google.service']._do_request(url, json.dumps(data), self.HEADERS_REQUEST, type='POST')

    def actualizar(self, file_id, data=None, params_query=None, user=None):
        url = "%s/files/%s?access_token=%s" % (self.BASE_URL_DRIVE, file_id, self.get_token(user))
        url += params_query if params_query else ''
        if not data:
            data = {}
        return self.env['google.service']._do_request(url, json.dumps(data), self.HEADERS_REQUEST, type='PATCH')

    def eliminar(self, file_id, user=None):
        url = "%s/files/%s?access_token=%s" % (self.BASE_URL_DRIVE, file_id, self.get_token(user))
        return self.env['google.service']._do_request(url, {}, self.HEADERS_REQUEST, type='DELETE')

    def get_token(self, user=None):
        user_action = user if user else self.env.user.sudo()
        if not user_action.google_gdrive_token_validity or \
            user_action.google_gdrive_token_validity < (datetime.now() + timedelta(minutes=1)):
            self.do_refresh_token(user_action)
            user_action.refresh()
        return user_action.google_gdrive_token

    def get_last_sync_date(self, user=None):
        user_action = user if user else self.env.user.sudo()
        return user_action.google_gdrive_last_sync_date and fields.Datetime.\
            from_string(user_action.google_gdrive_last_sync_date) + timedelta(minutes=0) or False

    def do_refresh_token(self, user=None):
        user_action = user if user else self.env.user.sudo()
        all_token = self.env['google.service']._refresh_google_token_json(user_action.google_gdrive_rtoken, self.STR_SERVICE)

        vals = {}
        vals['google_%s_token_validity' % self.STR_SERVICE] = datetime.now() + timedelta(seconds=all_token.get('expires_in'))
        vals['google_%s_token' % self.STR_SERVICE] = all_token.get('access_token')

        user_action.sudo().write(vals)

    def need_authorize(self, user=None):
        user_action = user if user else self.env.user.sudo()
        aa = user_action.sudo().google_gdrive_rtoken
        return aa is False

    def get_drive_scope(self, RO=False):
        readonly = '.readonly' if RO else ''
        return 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file'
        return 'https://www.googleapis.com/auth/drive%s' % (readonly)

    def authorize_google_uri(self, from_url='http://www.odoo.com'):
        url = self.env['google.service']._get_authorize_uri(from_url, self.STR_SERVICE, scope=self.get_drive_scope())
        return url

    def can_authorize_google(self):
        return self.env['res.users'].sudo().has_group('base.group_erp_manager')

    @api.model
    def set_all_tokens(self, authorization_code, user=None):
        user_action = user if user else self.env.user.sudo()
        all_token = self.env['google.service']._get_google_token_json(authorization_code, self.STR_SERVICE)

        vals = {}
        vals['google_%s_rtoken' % self.STR_SERVICE] = all_token.get('refresh_token')
        vals['google_%s_token_validity' % self.STR_SERVICE] = datetime.now() + timedelta(seconds=all_token.get('expires_in'))
        vals['google_%s_token' % self.STR_SERVICE] = all_token.get('access_token')
        user_action.sudo().write(vals)

