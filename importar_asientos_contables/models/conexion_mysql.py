# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import mysql.connector
from mysql.connector import (connection)
from mysql.connector import errorcode

_logger = logging.getLogger(__name__)


class ConexionMysql(object):
    def execute(self, query, params=None, commit=False):
        data = []
        try:
            cnx = connection.MySQLConnection(user='tetrace_gastos', password='felixV10A1973', host='hl238.dinaserver.com',
                                             database='tetrace_gastos')
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
