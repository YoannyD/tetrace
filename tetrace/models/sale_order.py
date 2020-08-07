# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ref_proyecto = fields.Char('Referencia proyecto')
    nombre_proyecto = fields.Char('Nombre proyecto')
    descripcion_proyecto = fields.Char('Descripción proyecto')
    cabecera_proyecto = fields.Html('Cabecera proyecto')

    _sql_constraints = [
        ('ref_proyecto_uniq', 'unique (ref_proyecto)', "¡La referencia de proyecto tiene que ser única!"),
    ]

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'ref_proyecto' in vals or 'nombre_proyecto' in vals:
            for r in self:
                if r.project_ids:
                    if not vals.get('ref_proyecto') or not vals.get('nombre_proyecto'):
                        raise ValidationError('La referencia y el nombre de proyecto son obligatorios.')

                    name = "%s %s" % (r.ref_proyecto, r.nombre_proyecto)
                    r.project_ids.write({'name': name})
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_project(self):
        self.ensure_one()
        if not self.order_id.ref_proyecto or not self.order_id.nombre_proyecto:
            raise ValidationError("Para crear el proyecto es obligatorio indicar el nombre y la referencia.")

        project = super(SaleOrderLine, self)._timesheet_create_project()
        name = "%s %s" % (self.order_id.ref_proyecto, self.order_id.nombre_proyecto)
        project.write({'name': name})
        return project
