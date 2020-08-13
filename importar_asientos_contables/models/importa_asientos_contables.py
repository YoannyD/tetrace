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
        if self.env.company != company_id:
            raise UserError("La compañia que se ha pasado como parámetro tiene que ser la misma que la seleccionada actualmente.")

        query = self._create_query(db_table, offset, limit, where, order)
        data = self.execute(db_name, db_user, db_pass, db_host, query)
        asientos_agrupados = self._agrupar_registros_por_asiento(data)

        for asiento, items in asientos_agrupados.items():
            ref_asiento = int(items[0]['numero_asiento'])

            journal = self.env['account.journal'].search([
                ('name', '=', items[0]['diario']),
                ('company_id', '=', company_id)
            ])
            if not journal:
                print("Para el asiento %s no se ha econtrado un diario." % ref_asiento)

            values_asiento = {
                'date': items[0]['fecha_asiento'].strftime("%Y-%m-%d"),
                'journal_id': journal.id,
                'ref': ref_asiento,
                'company_id': company_id
            }

            sin_cuenta = False
            values_lines = []
            for item in items:
                account = self._buscar_cuenta(item['cuenta'])
                if not account:
                    print("La cuenta %s del asiento %s no se ha econtrado." % (item['cuenta'], ref_asiento))
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
        cuenta = str(int(cuenta))
        cuenta_buscar = cuenta
        prefijo = cuenta[:4]
        if prefijo in ['4000', '4100', '4300', ]:
            cuenta_buscar = "%s0000000" % prefijo

        cuenta = self.env['account.account'].search([
            ('code', '=', cuenta_buscar),
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
        self.execute(db_name, db_user, db_pass, db_host, query)

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
