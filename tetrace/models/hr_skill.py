# -*- coding: utf-8 -*-
# © 2021 Vodoo - <hola@voodoo.es>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Skill(models.Model):
    _inherit = 'hr.skill'
    
    name = fields.Char(translate=True)
    

class SkillType(models.Model):
    _inherit = 'hr.skill.type'
    
    name = fields.Char(translate=True)
    

class SkillLevel(models.Model):
    _inherit = 'hr.skill.level'
    
    name = fields.Char(translate=True)