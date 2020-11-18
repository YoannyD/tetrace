# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _, tools

_logger = logging.getLogger(__name__)


class ProjectContract(models.Model):
    _name = 'tetrace.project_contract'
    _description = "Empleados proyecto"
    _auto = False
    _order = 'project_id, task_id'
    
    contract_id = fields.Many2one("hr.contract", string="Técnico", readonly=True)
    task_id = fields.Many2one("project.task", string="Tarea", readonly=True)
    project_id = fields.Many2one("project.project", string="Proyecto", readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                     CONCAT(tcr.task_id, tcr.contract_id, pp.id) as id,
                    tcr.task_id,
                    tcr.contract_id,
                    pp.id as project_id
                FROM task_contract_rel as tcr
                INNER JOIN project_task as pt ON tcr.task_id = pt.id
                INNER JOIN project_project as pp ON pt.project_id = pp.id
            )""" % (self._table))
        