# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>

import logging

from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from odoo import fields, http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)


class TetracePortal(CustomerPortal):
    
    def _prepare_home_portal_values(self):
        values = super(TetracePortal, self)._prepare_home_portal_values()
        
        equipment_count = request.env['maintenance.equipment'].sudo().search_count(['|',
            ('employee_id.user_id', '=', request.env.user.id),
            ('owner_user_id', '=', request.env.user.id)
        ])
        
        document_count = request.env['documents.document'].sudo().search_count([
            ('res_model', '=', 'hr.employee'),
            ('res_id', 'in', request.env.user.employee_ids.ids)
        ])
        
        values.update({
            'equipment_count': equipment_count,
            'document_count': document_count
        })
        
        return values
    
    @http.route(['/my/equipments', '/my/equipments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipments(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kw):
        Equipment = request.env['maintenance.equipment'].sudo()
        values = self._prepare_portal_layout_values()
        domain = ['|',
            ('employee_id.user_id', '=', request.env.user.id),
            ('owner_user_id', '=', request.env.user.id)
        ]

        searchbar_sortings = {
            'assign_date': {'label': _('Fecha de asignación'), 'order': 'assign_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }

        searchbar_inputs = {
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'category_id': {'input': 'category_id', 'label': _('Categoría')},
        }

        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [("assign_date", "=", today)]},
            'week': {'label': _('This week'), 'domain': [('assign_date', '>=', date_utils.start_of(today, "week")), ('assign_date', '<=', date_utils.end_of(today, 'week'))]},
            'month': {'label': _('This month'), 'domain': [('assign_date', '>=', date_utils.start_of(today, 'month')), ('assign_date', '<=', date_utils.end_of(today, 'month'))]},
            'year': {'label': _('This year'), 'domain': [('assign_date', '>=', date_utils.start_of(today, 'year')), ('assign_date', '<=', date_utils.end_of(today, 'year'))]},
            'quarter': {'label': _('This Quarter'), 'domain': [('assign_date', '>=', quarter_start), ('assign_date', '<=', quarter_end)]},
            'last_week': {'label': _('Last week'), 'domain': [('assign_date', '>=', date_utils.start_of(last_week, "week")), ('assign_date', '<=', date_utils.end_of(last_week, 'week'))]},
            'last_month': {'label': _('Last month'), 'domain': [('assign_date', '>=', date_utils.start_of(last_month, 'month')), ('assign_date', '<=', date_utils.end_of(last_month, 'month'))]},
            'last_year': {'label': _('Last year'), 'domain': [('assign_date', '>=', date_utils.start_of(last_year, 'year')), ('assign_date', '<=', date_utils.end_of(last_year, 'year'))]},
        }

        if not sortby:
            sortby = 'assign_date'
            
        order = searchbar_sortings[sortby]['order']

        if not filterby:
            filterby = 'all'
        domain = AND([domain, searchbar_filters[filterby]['domain']])

        if search and search_in:
            domain = AND([domain, [('name', 'ilike', search)]])

        equipment_count = Equipment.search_count(domain)

        pager = portal_pager(
            url="/my/equipments",
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search, 'filterby': filterby},
            total=equipment_count,
            page=page,
            step=self._items_per_page
        )

        if groupby == 'category_id':
            order = "category_id, %s" % order
        equipments = Equipment.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        if groupby == 'category_id':
            grouped_equipments = [Equipment.concat(*g) for k, g in groupbyelem(equipments, itemgetter('category_id'))]
        else:
            grouped_equipments = [equipments]

        values.update({
            'equipments': equipments,
            'grouped_equipments': grouped_equipments,
            'page_name': 'equipment',
            'default_url': '/my/equipments',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'search_in': search_in,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("tetrace.portal_my_equipments", values)
    
    @http.route(['/my/equipment/<int:equipment_id>'], type='http', auth="public", website=True)
    def portal_my_project(self, equipment_id=None, **kw):
        equipment = request.env['maintenance.equipment'].sudo().search([
            ('id', '=', equipment_id),
            '|',
            ('employee_id.user_id', '=', request.env.user.id),
            ('owner_user_id', '=', request.env.user.id)
        ], limit=1)
        
        if not equipment:
            return request.redirect('/my')

        return request.render("tetrace.portal_my_equipment", {
            'page_name': 'equipment',
            'equipment': equipment,
        })
    
    @http.route(['/my/documents', '/my/documents/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_documents(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kw):
        Document = request.env['documents.document'].sudo()
        values = self._prepare_portal_layout_values()
        domain = [
            ('res_model', '=', 'hr.employee'),
            ('res_id', 'in', request.env.user.employee_ids.ids)
        ]

        searchbar_sortings = {
            'create_date': {'label': _('Fecha creación'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }

        searchbar_inputs = {
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'folder_id': {'input': 'folder_id', 'label': _('Carpeta')},
        }

        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [("create_date", "=", today)]},
            'week': {'label': _('This week'), 'domain': [('create_date', '>=', date_utils.start_of(today, "week")), ('create_date', '<=', date_utils.end_of(today, 'week'))]},
            'month': {'label': _('This month'), 'domain': [('create_date', '>=', date_utils.start_of(today, 'month')), ('create_date', '<=', date_utils.end_of(today, 'month'))]},
            'year': {'label': _('This year'), 'domain': [('create_date', '>=', date_utils.start_of(today, 'year')), ('create_date', '<=', date_utils.end_of(today, 'year'))]},
            'quarter': {'label': _('This Quarter'), 'domain': [('create_date', '>=', quarter_start), ('create_date', '<=', quarter_end)]},
            'last_week': {'label': _('Last week'), 'domain': [('create_date', '>=', date_utils.start_of(last_week, "week")), ('create_date', '<=', date_utils.end_of(last_week, 'week'))]},
            'last_month': {'label': _('Last month'), 'domain': [('create_date', '>=', date_utils.start_of(last_month, 'month')), ('create_date', '<=', date_utils.end_of(last_month, 'month'))]},
            'last_year': {'label': _('Last year'), 'domain': [('create_date', '>=', date_utils.start_of(last_year, 'year')), ('create_date', '<=', date_utils.end_of(last_year, 'year'))]},
        }

        if not sortby:
            sortby = 'create_date'
            
        order = searchbar_sortings[sortby]['order']

        if not filterby:
            filterby = 'all'
        domain = AND([domain, searchbar_filters[filterby]['domain']])

        if search and search_in:
            domain = AND([domain, [('name', 'ilike', search)]])

        document_count = Document.search_count(domain)

        pager = portal_pager(
            url="/my/documents",
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search, 'filterby': filterby, 'groupby': groupby},
            total=document_count,
            page=page,
            step=self._items_per_page
        )

        if groupby == 'folder_id':
            order = "folder_id, %s" % order
        documents = Document.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        if groupby == 'folder_id':
            grouped_documents = [Document.concat(*g) for k, g in groupbyelem(documents, itemgetter('folder_id'))]
        else:
            grouped_documents = [documents]

        values.update({
            'documents': documents,
            'grouped_documents': grouped_documents,
            'page_name': 'document',
            'default_url': '/my/documents',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'search_in': search_in,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("tetrace.portal_my_documents", values)