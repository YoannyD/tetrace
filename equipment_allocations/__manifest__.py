# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Equipment Allocations",
  "summary"              :  """The module provides a way to manage workplace equipments. The user can enter the repective request for an equipment allocation to an employee.""",
  "category"             :  "Human Resources",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Equipment-Allocations.html",
  "description"          :  """Odoo Equipment Allocations
Manage office equipment in odoo
Maintain equipment records in Odoo
Odoo equipment allocation records
Lend equipment to employees
Assign equipment to employees""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=equipment_allocations",
  "depends"              :  [
                             'hr_maintenance',
                             'stock',
                             'account',
                            ],
  "data"                 :  [
                             'edi/mail_template.xml',
                             'security/maintenance_security.xml',
                             'security/ir.model.access.csv',
                             'wizard/wizard_view.xml',
                             'wizard/allocation_wizard_view.xml',
                             'wizard/replace_equipment_view.xml',
                             'views/wk_maintenance.xml',
                            ],
  "demo"                 :  ['data/demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  45,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}