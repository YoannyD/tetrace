# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _, tools

_logger = logging.getLogger(__name__)


class ProjectApplicant(models.Model):
    _name = 'tetrace.project_applicant'
    _description = "Procesos de selección proyecto"
    _auto = False
    _order = 'project_id, task_id'
    
    applicant_id = fields.Many2one("hr.applicant", string="Proceso selección", readonly=True)
    task_id = fields.Many2one("project.task", string="Tarea", readonly=True)
    project_id = fields.Many2one("project.project", string="Proyecto", readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                     CONCAT(tar.task_id, tar.applicant_id, pp.id) as id,
                    tar.task_id,
                    tar.applicant_id,
                    pp.id as project_id
                FROM task_applicant_rel as tar
                INNER JOIN project_task as pt ON tar.task_id = pt.id
                INNER JOIN project_project as pp ON pt.project_id = pp.id
            )""" % (self._table))
        