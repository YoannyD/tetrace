# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ReportProductAssignation(models.AbstractModel):
    _name = 'report.stock_employee_product_assignation.pa_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        assignations = self.env['stock.product.assignation'].browse(docids)
        employees = assignations.mapped('employee_id')
        projects = assignations.mapped('request_id.project_id')
        if any(a.assignation_return for a in assignations):
            raise ValidationError(_('You must select non returned assignations!'))
        if len(employees) > 1:
            raise ValidationError(_('You must select assignations for the same employee!'))
        if len(projects) > 1:
            raise ValidationError(_('You must select assignations for the same project!'))
        return {
            'doc_ids': docids,
            'doc_model': self.env['stock.product.assignation'],
            'data': data,
            'docs': assignations,
        }
