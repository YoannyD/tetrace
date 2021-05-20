# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountChangeLockDate(models.TransientModel):
    _inherit = "account.change.lock.date"
    
    fecha_bloque_imputacion_horas = fields.Date("Fecha bloqueo imputación horas", 
                                                default=lambda self: self.env.company.fecha_bloque_imputacion_horas)
    
    def change_lock_date(self):
        companies = self.env['res.company'].sudo().search([])
        companies.write({'fecha_bloque_imputacion_horas': self.fecha_bloque_imputacion_horas})
        return super(AccountChangeLockDate, self).change_lock_date()