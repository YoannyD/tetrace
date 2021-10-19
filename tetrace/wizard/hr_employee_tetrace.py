# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class hr_employee_tetrace(models.TransientModel):
    _name = "hr.employee.tetrace"
    
    language = fields.Selection([('spanish', 'Español'), ('english', 'Inglés')])
    
    
    def print_report(self):
        print('holaaaa', self.read()[0])
        data = {}
        if self.language == 'spanish':
            return self.env.ref('tetrace.action_report_curriculum').report_action([], data=data)
        else:
            return self.env.ref('tetrace.action_report_curriculum_english').report_action([], data=data)
        
        