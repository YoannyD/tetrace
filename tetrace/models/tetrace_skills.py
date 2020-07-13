# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Skill(models.Model):
    _name = 'tetrace.skill'
    _description = "Applications Skill"

    name = fields.Char(required=True)
    skill_type_id = fields.Many2one('hr.skill.type')


class ApplicationSkill(models.Model):
    _name = 'tetrace.applicant.skill'
    _description = "Habilidades de un solicitud"
    _rec_name = 'skill_id'
    _order = "skill_level_id"

    applicant_id = fields.Many2one('hr.applicant', required=True, ondelete='cascade')
    skill_id = fields.Many2one('tetrace.skill', required=True)
    skill_level_id = fields.Many2one('tetrace.skill.level', required=True)
    skill_type_id = fields.Many2one('tetrace.skill.type', required=True)
    level_progress = fields.Integer(related='skill_level_id.level_progress')

    _sql_constraints = [
        ('_unique_skill', 'unique (application_id, skill_id)', "Two levels for the same skill is not allowed"),
    ]

    @api.constrains('skill_id', 'skill_type_id')
    def _check_skill_type(self):
        for record in self:
            if record.skill_id not in record.skill_type_id.skill_ids:
                raise ValidationError(_("The skill %s and skill type %s doesn't match") % (record.skill_id.name, record.skill_type_id.name))

    @api.constrains('skill_type_id', 'skill_level_id')
    def _check_skill_level(self):
        for record in self:
            if record.skill_level_id not in record.skill_type_id.skill_level_ids:
                raise ValidationError(_("The skill level %s is not valid for skill type: %s ") % (record.skill_level_id.name, record.skill_type_id.name))


class SkillLevel(models.Model):
    _name = 'tetrace.skill.level'
    _description = "Skill Level"
    _order = "level_progress desc"

    skill_type_id = fields.Many2one('tetrace.skill.type')
    name = fields.Char(required=True)
    level_progress = fields.Integer(string="Progress", help="Progress from zero knowledge (0%) to fully mastered (100%).")


class SkillType(models.Model):
    _name = 'tetrace.skill.type'
    _description = "Skill Type"

    name = fields.Char(required=True)
    skill_ids = fields.One2many('tetrace.skill', 'skill_type_id', string="Skills", ondelete='cascade')
    skill_level_ids = fields.One2many('tetrace.skill.level', 'skill_type_id', string="Levels", ondelete='cascade')
