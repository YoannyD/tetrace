# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TipoProyecto(models.Model):
    _name = "tetrace.tipo_proyecto"
    _description = "Tipos de proyecto"
    _rec_name = 'tipo'

    name = fields.Char('Nombre', required=True, translate=True)
    tipo = fields.Char('Tipo', required=True, translate=True)
    sale_order_ids = fields.One2many('sale.order', 'tipo_proyecto_id')
    purchase_order_ids = fields.One2many('purchase.order', 'tipo_proyecto_id')
    account_move_ids = fields.One2many('account.move', 'tipo_proyecto_id')
    tipo_servicio_ids = fields.Many2many("tetrace.tipo_servicio")

    def name_get(self):
        res=[]
        for rec in self:
            if self.env.context.get('display_tipo', False):
                display_name = rec.tipo
            elif self.env.context.get('display_name', False):
                display_name = rec.name
            else:
                display_name = '%s %s' % (rec.tipo, rec.name)
            res.append((rec.id, display_name))
        return res
    
    @api.constrains("tipo")
    def _check_tipo(self):
        for r in self:
            if r.tipo and len(r.tipo) != 2:
                raise UserError(_('El tipo tiene que ser 2 caracteres.'))
