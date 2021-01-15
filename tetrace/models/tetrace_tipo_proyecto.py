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

    def name_get(self):
        res=[]
        for rec in self:
            if self.env.context.get('mostrar_tipo_nombre', False):
                res.append((rec.id, '%s %s' % (rec.tipo, rec.name)))
            else:
                res.append((rec.id, rec.tipo))
        return res
    
    @api.constrains("tipo")
    def _check_tipo(self):
        for r in self:
            if r.tipo and len(r.tipo) != 2:
                raise UserError(_('El tipo tiene que ser 2 caracteres.'))
