# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"
    
    equipment_assign_to = fields.Selection(selection_add=[('project', 'Proyecto'), ('tecnico_proyecto', 'Técnico proyecto')])
    project_id = fields.Many2one("project.project", string="Proyecto")
    project_tecnico_ids = fields.Many2many('hr.employee', related="project_id.tecnico_ids")
    tecnico_id = fields.Many2one("hr.employee", string="Técnico proyecto")
    