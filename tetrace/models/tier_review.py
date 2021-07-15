# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class TierReview(models.Model):
    _inherit = "tier.review"
    
    def write(self, vals):
        res = super(TierReview, self).write(vals)
        if 'status' in vals:
            self.actualizar_estado_factura()
        return res
    
    def actualizar_estado_factura(self):
        for r in self:
            if r.model != 'account.move':
                continue
                
            reviews = self.search_count([
                ('model', '=', 'account.move'),
                ('res_id', '=', r.res_id),
                ('status', '!=', 'approved'),
            ])

            if reviews == 0:
                move = self.env['account.move'].browse(r.res_id)
                move.write({'estado_tetrace': 'validada'})