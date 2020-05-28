# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

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
            status, response, ask_time = GoogleDrive.obtener(carpeta_padre, None, self.env.user)
            _logger.warning(response)
            pass
