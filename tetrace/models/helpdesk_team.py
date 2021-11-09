# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"
    
    def _get_reabrir_stage(self):
        reabrir_stage = self.stage_ids.filtered(lambda stage: stage.es_reabrir)
        if not reabrir_stage:
            reabrir_stage = self.stage_ids[-1]
        return reabrir_stage