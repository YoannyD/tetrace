# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#    Globalteckz                                                              #
#    Copyright (C) 2013-Today Globalteckz (http://www.globalteckz.com)        #
#                                                                             #   
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU Affero General Public License as           #
#    published by the Free Software Foundation, either version 3 of the       #
#    License, or (at your option) any later version.                          #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU Affero General Public License for more details.                      #
#                                                                             #  
#    You should have received a copy of the GNU Affero General Public License #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #           
###############################################################################
{
    'name': "Merge multiple Picking",
    'summary': """This module will help you to handle large picking and merge in single picking""",
    'description': """
merge picking
picking merge
merging
pick list merge
picklist merge
    """,
    'author': "Globalteckz",
    'website': "http://www.globalteckz.com",
    'category': 'Uncategorized',
    'version': '13.0.1',
    "license" : "Other proprietary",
    'images': ['static/description/banner.png'],
    "price": "39.00",
    "currency": "EUR",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        'views/merge_picking.xml'
       
    ],
  
}
