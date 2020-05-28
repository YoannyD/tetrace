# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import json
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Applicant(models.Model):
    _inherit = "hr.applicant"

    country_id = fields.Many2one('res.country', string="País")
    job_ids = fields.Many2many('hr.job', 'applicant_id', string="Otro puesto de trabajo")
    carpeta_drive = fields.Char('Carpeta Drive')
    fecha_recepcion = fields.Date('Fecha recepción')

    def importar_ficheros_drive(self):
        GoogleDrive = self.env['google.gdrive'].sudo()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        carpeta_padre = get_param('google_gdrive_carpeta', default='')
        for r in self.filtered(lambda x: x.carpeta_drive):
            params = "&q='%s' in parents and fullText contains '%s'" % (carpeta_padre, r.carpeta_drive)
            status, response, ask_time = GoogleDrive.buscar(params, self.env.user)
            _logger.warning("primera busqueda")
            _logger.warning(response)
            if response:
                # data = json.loads(response)
                for file in response['files']:
                    _logger.warning(file['name'].strip() == r.carpeta_drive.strip())
                    #                     if file['name'].strip() == r.carpeta_drive.strip():
                    _logger.warning("carpeta encontrada")
                    params2 = "&q='%s' in parents" % file['id']
                    status2, response2, ask_time2 = GoogleDrive.buscar(params2, self.env.user)
                    _logger.warning(response2)
                    if response2:
                        for file2 in response2['files']:
                            params3 = '&alt=media&acknowledgeAbuse=true'
                            status3, response3, ask_time3 = GoogleDrive.export(file2['id'], params3, self.env.user)
#                                 _logger.warning(response3)

