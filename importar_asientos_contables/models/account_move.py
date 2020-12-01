# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import mysql.connector

from mysql.connector import (connection)
from mysql.connector import errorcode
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    cuadrar_blanceo = fields.Boolean("Cuadrar balanceo")