# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ResCompany(models.Model):
    _inherit = 'res.company'

    warehouse_sign = fields.Binary(string='Sign')
    warehouse_responsible_id = fields.Many2one('hr.employee', string='Warehouse responsible')
    legal_dispositions = fields.Text(string='Legal dispositions')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    legal_dispositions = fields.Text(related='company_id.legal_dispositions', readonly=False, store=True)
    warehouse_sign = fields.Binary(related='company_id.warehouse_sign', readonly=False, store=True)
    warehouse_responsible_id = fields.Many2one('hr.employee', related='company_id.warehouse_responsible_id',
                                               readonly=False, store=True)
    warehouse_sign_filename = fields.Char()

    @api.onchange('warehouse_sign')
    def onchange_warehouse_sign(self):
        if self.warehouse_sign:
            filename = self.warehouse_sign_filename
            if filename:
                jpg = filename.find('.jpg')
                jpeg = filename.find('.jpeg')
                png = filename.find('.png')
                file_type = False
                if jpg != -1 and filename.endswith('pg'):
                    file_type = 'jpg'
                elif jpeg != -1 and filename.endswith('eg'):
                    file_type = 'jpeg'
                elif png != -1:
                    file_type = 'png'
                if not file_type:
                    self.warehouse_sign = None
                    self.warehouse_sign_filename = None
                    raise UserError(_('The file extension is not allowed, only accept [jpg, jpeg, png].'))
