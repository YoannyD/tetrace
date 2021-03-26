# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo.http import request

_logger = logging.getLogger(__name__)


def create_domain(filtros):
    if not filtros:
        return []

    if not isinstance(filtros[0], list) and filtros[0] == '!':
        return parse_filtros(filtros, '!=')
    elif not isinstance(filtros[0], list):
        return parse_filtro(filtros)

    domain = parse_filtros(filtros)
    return domain

def parse_filtros(filtros, condition_force=None):
    domain = []

    if not condition_force:
        for item in filtros:
            if item == 'or':
                domain += '|'
            elif item == 'and':
                domain += '&'

    i = 0
    for filtro in filtros:
        if (isinstance(filtro, list) and filtro[0] == '!') or filtro == '!':
            domain += parse_filtro(filtros[i], '!=')
        elif isinstance(filtro, list):
            if isinstance(filtro[0], list):
                domain += parse_filtros(filtro, condition_force)
            else:
                domain += parse_filtro(filtro, condition_force)
        i += 1
    return domain

def parse_filtro(filtro, condition_force=None):
    if isinstance(filtro, list) and filtro[0] == '!':
        if len(filtro[1]) == 1:
            return parse_filtro(filtro[1], '!=')
        else:
            return parse_filtros(filtro[1], '!=')

    if isinstance(filtro, list) and len(filtro) == 3:
        valor = filtro[2]
        if condition_force:
            condition = condition_force
        elif filtro[1] == 'contains':
            condition = 'ilike'
        elif filtro[1] == 'notcontains':
            condition = ' not ilike'
        elif filtro[1] == 'startswith':
            condition = '=ilike'
            valor = str(filtro[2]) + '%'
        elif filtro[1] == 'endswith':
            condition = '=ilike'
            valor = '%' + str(filtro[2])
        elif filtro[1] == '<>':
            condition = '!='
        else:
            condition = filtro[1]

        return [(filtro[0], condition, valor)]
    return []

def data_groups(res_model, grupos, domain, nivel, fields_exception=[]):
    if not grupos or (nivel + 1) > len(grupos):
        return None, None

    campo_group = grupos[nivel]['selector']
    if grupos[nivel] and 'desc' in grupos[nivel] and grupos[nivel]['desc']:
        order_group = 'desc'
    else:
        order_group = 'asc'

    Model = request.env[res_model].sudo()
    records = Model.read_group(
        domain=domain,
        fields=[campo_group],
        groupby=[campo_group],
        orderby='%s %s' % (campo_group, order_group)
    )

    total_count = 0
    group_count = 0
    items = []
    for r in records:
        if r[campo_group]:
            if campo_group in fields_exception:
                key = r[campo_group][1]
            else:
                key = r[campo_group]
        elif r[campo_group] == '':
            key = 'Vacio'
        else:
            key = 'No definido'
        items.append({
            'key': key,
            'items': data_groups(res_model, grupos, domain, nivel + 1),
            'count': r['%s_count' % campo_group],
            'summary': [r['%s_count' % campo_group]]
        })
        total_count += r['%s_count' % campo_group]
        group_count += 1

    if nivel > 0:
        return items

    return {
        'data': items,
        'totalCount': total_count,
        'groupCount': group_count,
    }
