# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    secuencia_default_code = fields.Integer('Secuencia Ref. Interna', copy=False)
    project_template_id = fields.Many2one("project.project", string="Plantilla proyecto confirmado")
    project_template_diseno_id = fields.Many2one("project.project", string="Plantilla proyecto preliminar")
    producto_entrega = fields.Boolean("Producto entrega", compute="_compute_producto_entrega", store=True)
    individual = fields.Boolean("Individual")
    archivar_order_line = fields.Boolean("Archivados en líneas de venta")

    @api.depends("service_policy", "service_tracking")
    def _compute_producto_entrega(self):
        for r in self:
            if r.service_policy == 'delivered_manual' and \
                r.service_tracking == 'task_in_project':
                r.producto_entrega = True
            else:
                r.producto_entrega = False
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        self = self.with_context(force_company=19)
        return super(ProductTemplate, self)._search(args, offset, limit, order, count, access_rights_uid)

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        if not res.default_code:
            secuencia, default_code = res.generar_default_code(False)
            res.write({
                'default_code': default_code,
                'secuencia_default_code': secuencia,
            })
        return res

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if 'type' in vals or 'categ_id' in vals:
            for r in self:
                secuencia, default_code = r.generar_default_code(True)
                r.write({
                    'default_code': default_code,
                    'secuencia_default_code': secuencia
                })
        return res

    def generar_default_code(self, update=False):
        self.ensure_one()
        tipo = ''
        if self.type == 'consu':
            tipo = "C"
        elif self.type == 'service':
            tipo = "S"
        elif self.type == 'product':
            tipo = "P"

        categoria = self.categ_id.referencia if self.categ_id and self.categ_id.referencia else '00'

        def secuencia_str(code):
            caracteres = len(str(code))
            secuencia = code + 1
            for num in range(0, (5 - caracteres)):
                secuencia = "0%s" % secuencia
            return secuencia

        if update and self.secuencia_default_code:
            secuencia = secuencia_str(self.secuencia_default_code)
            secuencia_int = self.secuencia_default_code
        else:
            ultimo_producto = self.search([('secuencia_default_code', '!=', False)],
                                          order="secuencia_default_code desc", limit=1)
            if ultimo_producto:
                secuencia = secuencia_str(ultimo_producto.secuencia_default_code)
                secuencia_int = ultimo_producto.secuencia_default_code
            else:
                secuencia = "00001"
                secuencia_int = 1
            secuencia_int = secuencia_int + 1

        code = "%s-%s-%s" % (tipo, categoria, secuencia)
        return secuencia_int, code
