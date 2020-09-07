# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ref_proyecto = fields.Char('Referencia proyecto', copy=False)
    nombre_proyecto = fields.Char('Nombre proyecto', copy=False)
    descripcion_proyecto = fields.Char('Descripción proyecto', copy=False)
    cabecera_proyecto = fields.Html('Cabecera proyecto', copy=False)

    _sql_constraints = [
        ('ref_proyecto_uniq', 'unique (ref_proyecto)', "¡La referencia de proyecto tiene que ser única!"),
    ]

    @api.constrains("ref_proyecto")
    def _check_ref_proyecto(self):
        msg_error = "La referencia tiene que tener el formato 0000.0000"
        for r in self:
            if r.ref_proyecto:
                if r.ref_proyecto.find('.') != 4 or len(r.ref_proyecto) != 9:
                    raise ValidationError(msg_error)

                aux = r.ref_proyecto.split(".")
                for a in aux:
                    try:
                        int(a)
                    except:
                        raise ValidationError(msg_error)

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'ref_proyecto' in vals or 'nombre_proyecto' in vals:
            self.actualizar_datos_proyecto()
        return res

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        _logger.warning("fffffff")
        self.actualizar_datos_proyecto()
        return res

    def actualizar_datos_proyecto(self):
        for r in self:
            if r.project_ids:
                if not r.ref_proyecto or not r.nombre_proyecto:
                    raise ValidationError('La referencia y el nombre de proyecto son obligatorios.')

                name = "%s %s" % (r.ref_proyecto, r.nombre_proyecto)
                r.project_ids.write({'name': name})
                for p in r.project_ids:
                    p.analytic_account_id.write({'name': r.ref_proyecto})


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
