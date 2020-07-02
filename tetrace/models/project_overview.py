# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = 'project.project'

    def _table_get_empty_so_lines(self):
        """ get the Sale Order Lines having no timesheet but having generated a task or a project """
        so_lines = self.sudo()\
            .mapped('sale_line_id.order_id.order_line')\
            .filtered(lambda sol: sol.is_service and sol.product_id.service_policy == 'delivered_timesheet' and not sol.is_expense and not sol.is_downpayment)
        # include the service SO line of SO sharing the same project
        sale_order = self.env['sale.order'].search([('project_id', 'in', self.ids)])
        return set(so_lines.ids) | set(sale_order.mapped('order_line').filtered(lambda sol: sol.is_service and sol.product_id.service_policy == 'delivered_timesheet' and not sol.is_expense).ids), set(
            so_lines.mapped('order_id').ids) | set(sale_order.ids)

    def _table_get_line_values(self):
        result = super(Project, self)._table_get_line_values()

        timesheet_forecast_table_rows = []
        for row in result['rows']:
            new_row = row
            if row[0]['res_id'] and row[0]['res_model'] == 'sale.order.line':
                sale_line_id = self.env['sale.order.line'].sudo().browse(row[0]['res_id'])
                if sale_line_id:
                    new_row[7] = sale_line_id.qty_delivered
                    new_row[8] = sale_line_id.qty_invoiced - sale_line_id.qty_delivered

            timesheet_forecast_table_rows.append(new_row)

        return {
            'header': result['header'],
            'rows': timesheet_forecast_table_rows
        }

