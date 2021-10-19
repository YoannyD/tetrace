# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class hr_applicant_tetrace(models.TransientModel):
    _name = "hr.applicant.tetrace"
    
    language = fields.Selection([('spanish', 'Español'), ('english', 'Inglés')])
    
    
    def print_report(self):
        print('holaaaa', self.read()[0])
        data = {}
        if self.language == 'spanish':
            return self.env.ref('tetrace.action_report_curriculum_applicant').report_action([], data=data)
        else:
            return self.env.ref('tetrace.action_report_curriculum_applicant_english').report_action([], data=data)
        