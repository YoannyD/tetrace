# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class hr_applicant_wizard(models.TransientModel):
    _name = "hr.applicant.wizard"
    
    def _default_emp_id(self):
        active_id = self.env.context.get('active_id')
        print('aquiiiiiiiiiiiiiiiiiiiiii', active_id)
        if active_id:
            record = self.env['hr.applicant'].browse(active_id)            
            return record.emp_id and record.emp_id.id or False
        return False
    
    language = fields.Selection([('spanish', 'Español'), ('english', 'Inglés')])
    emp_id= fields.Many2one(
        'hr.employee', string="Employee", default=_default_emp_id)
    
    def print_report(self):
        print('holaaaa', self.read()[0])
        data = {}
        if self.language == 'spanish':
            return self.env.ref('tetrace.action_report_curriculum_applicant_name').report_action([], data=data)
        else:
            return self.env.ref('tetrace.action_report_curriculum_applicant_name_english').report_action([], data=data)
    
    def cancel(self):
        return {'type': 'ir.actions.act_window_close'}