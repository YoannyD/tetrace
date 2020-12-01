# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import mysql.connector

from mysql.connector import (connection)
from mysql.connector import errorcode
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportarAsientosContables(models.AbstractModel):
    _name = 'importar_asientos_contables.importar'
    _description = "Importar asientos contables"

    @api.model
    def importar(self, db_name, db_user, db_pass, db_host, db_table, company_id, offset=0, limit=100000, where='', order=''):
        if self.env.company.id != company_id:
            raise UserError("La compañia que se ha pasado como parámetro tiene que ser la misma que la seleccionada actualmente.")

        query = self._create_query(db_table, offset, limit, where, order)
        data = self.execute(db_name, db_user, db_pass, db_host, query)
        if not data:
            return
        
        nums_asiento = [item['numero_asiento'] for item in data]
        where2 = " where numero_asiento IN (%s)" % ','.join(str(a) for a in nums_asiento)
        query = self._create_query(db_table, where=where2)
        data = self.execute(db_name, db_user, db_pass, db_host, query)
        
        asientos_agrupados = self._agrupar_registros_por_asiento(data)

        for asiento, items in asientos_agrupados.items():
            ref_asiento = items[0]['numero_asiento']

            journal = self.env['account.journal'].search([
                ('name', '=', items[0]['diario']),
                ('company_id', '=', company_id)
            ])
            if not journal:
                _logger.warning("Para el asiento %s no se ha econtrado un diario." % ref_asiento)

            values_asiento = {
                'date': items[0]['fecha_asiento'].strftime("%Y-%m-%d"),
                'journal_id': journal.id,
                'ref': ref_asiento,
                'company_id': company_id
            }

            sin_cuenta = False
            values_lines = []
            for item in items:
                account = self._buscar_cuenta(item['cuenta'], company_id)
                if not account:
                    _logger.warning("La cuenta %s del asiento %s no se ha econtrado." % (item['cuenta'], ref_asiento))
                    sin_cuenta = True
                    break

                partner_id = False
                if item['empresa']:
                    partner = self.env['res.partner'].search([
                        ('name', '=', item['empresa']),
                    ], limit=1)
                    if partner:
                        partner_id = partner.id

                values_apunte = (0, 0, {
                    'account_id': account.id,
                    'partner_id': partner_id,
                    'company_id': company_id,
                    'name': item['descripcion'] or False,
                    'debit': abs(float(item['debe'])),
                    'credit': abs(float(item['haber']))
                })
                values_lines.append(values_apunte)

            if sin_cuenta:
                self._marcar_registro(db_name, db_user, db_pass, db_host, db_table, ref_asiento, 2)
                continue

            values_asiento.update({'line_ids': values_lines})
            try:
                asiento = self.env['account.move'].create(values_asiento)
                traspasado = 1 if asiento else 3
                self._marcar_registro(db_name, db_user, db_pass, db_host, db_table, ref_asiento, traspasado)
            except:
                self._marcar_registro(db_name, db_user, db_pass, db_host, db_table, ref_asiento, 3)

    def _buscar_cuenta(self, cuenta, company_id):
        cuenta = cuenta

        cuenta = self.env['account.account'].search([
            ('code', '=', cuenta),
            ('company_id', '=', company_id)
        ], limit=1)
        return cuenta

    def _create_query(self, db_table, offset=0, limit=100000, where='', order=''):
        query = "SELECT * FROM %s" % db_table
        if where:
            query += where

        query += " limit %s,%s " % (offset, limit)
        if order:
            query += " order %s" % order

        return query

    def _agrupar_registros_por_asiento(self, data):
        asientos_agrupados = {}
        for item in data:
            key = str(item['numero_asiento'])
            if key not in asientos_agrupados:
                asientos_agrupados.update({key: []})
            asientos_agrupados[key].append(item)
        return asientos_agrupados

    def _marcar_registro(self, db_name, db_user, db_pass, db_host, db_table, ref_asiento, traspasado):
        query = "UPDATE %s SET traspaso = %s where numero_asiento = %s;" % (db_table, traspasado, ref_asiento)
        self.execute(db_name, db_user, db_pass, db_host, query, commit=True)

    @api.model
    def actualizar_apuntes_desde_mysql(self, db_name, db_user, db_pass, db_host, db_table, company_id, offset=0, limit=100000, where='', order=''):
        rs = self.env['account.move.line'].search([
            ('date', '>=', '2020-01-01'),
            ('date', '<=', '2020-12-31'),
            ('analytic_account_id', '=', False),
            ('analytic_tag_ids', '=', False),
            ('move_id.ref', '!=', False),
            ('company_id', '=', 1),
            '|',
            ('l10n_pe_group_id', 'like', '6%'),
            ('l10n_pe_group_id', 'like', '7%'),
#             ('ref', '=', '1'),
        ], limit=100)
        
        for r in rs:
            ref = r.move_id.ref

            sql = """
                SELECT 
                    APUNTES_CONTABLES.FECHA_APUNTE, 
                    APUNTES_CONTABLES.ASIENTO,
                    APUNTES_CONTABLES.CUENTA, 
                    ANALITICA.DISTRIBUCIÓN_ASIGNADA, 
                    ANALITICA.DEBE_HABER,
                    ANALITICA.IMPORTE, 
                    ANALITICA.PORCENTAJE_REP 
                FROM 
                    `APUNTES_CONTABLES` INNER JOIN ANALITICA on 
                    APUNTES_CONTABLES.FECHA_APUNTE = ANALITICA.FECHA_ASIENTO and 
                    APUNTES_CONTABLES.REFERENCIA_ASIENTO = ANALITICA.REFERENCIA_ASIENTO 
                where
                    APUNTES_CONTABLES.ASIENTO = """ + str(ref) 
            
            data = self.execute(db_name, db_user, db_pass, db_host, sql)
#             _logger.warning(sql)
            if not data:
                continue
            _logger.warning("con items")
            values = [(2, r.id)]  
            for item in data:
                analytic_account = self.env['account.analytic.account'].search([
                    ('code', '=', item['DISTRIBUCIÓN_ASIGNADA']),
                    '|',
                    ('company_id','=', False),
                    ('company_id','=', 1),
                ], limit=1)
                debe = 0
                haber = 0
                if r.debit > 0:
                    debe = item['IMPORTE']
                else:
                    haber = item['IMPORTE']
                
                values.append((0, 0, {
                    'account_id': r.account_id.id,
                    'partner_id': r.partner_id.id if r.partner_id else None,
                    'company_id': r.company_id.id if r.company_id else None,
                    'analytic_account_id': analytic_account.id if analytic_account else None,
                    'name': r.name,
                    'debit': abs(float(debe)),
                    'credit': abs(float(haber))
                }))            
            try:
                r.move_id.button_draft()
                r.move_id.write({'line_ids': values})
            except:
                _logger.warning(sql)
                _logger.warning("Referencia erronea %s" % ref)
                
        
    def execute(self, db_name, db_user, db_pass, db_host, query, params=None, commit=False):
        data = []
        try:
            cnx = connection.MySQLConnection(user=db_user, password=db_pass, host=db_host, database=db_name)
            cursor = cnx.cursor(dictionary=True)
            cursor.execute(query, params)

            if commit:
                cnx.commit()
            else:
                for rs in cursor:
                    data.append(rs)

            cursor.close()
            cnx.close()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                _logger.error("El usuario o contraseña para conectarse a la base de datos no son válidos")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                _logger.error("La base de datos no existe.")
            else:
                _logger.error(err)
        else:
            cnx.close()

        return True if commit else data
