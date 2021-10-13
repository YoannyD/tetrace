import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class hr_applicant_wizard(models.TransientModel):
    _name = "hr.applicant.wizard"
    
    language = fields.Selection([('english', 'Inglés'), ('spanish', 'Español')])
    
    
    def print_report(self):
        print('holaaaa', self.read()[0])
        data = {}
        return self.env.ref('tetrace.action_report_curriculum_applicant_name').report_action([], data=data)
        