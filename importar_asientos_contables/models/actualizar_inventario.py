# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import mysql.connector

from mysql.connector import (connection)
from mysql.connector import errorcode
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ActualizarInventario(models.AbstractModel):
    _name = 'actualizar_inventario.actualizar'
    _description = "Actualizar Inventario desde MySQL"

    @api.model
    def actualizar_productos(self, db_name, db_user, db_pass, db_host, db_table, offset=0, limit=100000, where='', order=''):  
        query = self._create_query(db_table, offset, limit, where, order)
        data = self.execute(db_name, db_user, db_pass, db_host, query)
        if not data:
            return
        for item in data:
            producto = self.env['product.template'].search([
                ('id', '=', item['idProducto'])
            ], limit=1)
            if producto:
                #categoria = self.env['product.category'].search([('complete_name','=', item['categoria'])])
                #fabricante = self.env['res.partner'].search([('name','=', item['fabricante'])])
                producto.write({
                    #'name' : item['nombreProductoNuevo'],
                    #'categ_id' : categoria.id if categoria else False,
                    #'manufacturer' : fabricante.id if fabricante else False,
                    #'manufacturer_pname' : item['modelo'],
                    'standard_price' : item['valorUnitario'],
                })
                _logger.warning("Producto original %s actualizado" % item['idProducto'])
                self._marcar_registro(db_name, db_user, db_pass, db_host, db_table, item['idProducto'])
        
    @api.model
    def importar_lineas_inventario(self, db_name, db_user, db_pass, db_host, db_table, offset=0, limit=100000, where='', order=''):  
        query = self._create_query(db_table, offset, limit, where, order)
        data = self.execute(db_name, db_user, db_pass, db_host, query)
        if not data:
            return
        linea_inventario = self.env['stock.inventory.line']
        for item in data:
            _logger.warning("Procesando línea %s " % item['linea_id'])
            producto_plantilla = self.env['product.template'].search([('id','=', item['producto_template_id'])])
            if producto_plantilla.type !='product':
                #No podemos añadir la línea de inventario ya que el producto no es almacenable
                #Marcamos el registro con 3
                self._marcar_registro_inventario(db_name, db_user, db_pass, db_host, db_table, 3, item['linea_id'])
                continue
            lote = self.env['stock.production.lot'].search([('product_id','=',item['product_id']),('name','=',item['lote'])], limit = 1)
            if lote == False and producto_plantilla.tracking in ['serial','lot']:
                #No podemos añadir la línea de inventario ya que el producto requiere de un numero de serie o lote y no lo tenemos
                #Marcamos el registro con 4
                self._marcar_registro_inventario(db_name, db_user, db_pass, db_host, db_table, 4, item['linea_id'])
                continue
            ubicacion = self.env['stock.location'].search([('name','=', item['ubicacion'])], limit = 1)
            linea_inventario_existente = linea_inventario.search([('inventory_id','=', item['inventory_id']),\
                                                                  ('location_id','=', ubicacion.id if ubicacion else 8),\
                                                                  ('product_id','=', item['product_id']),\
                                                                  ('prod_lot_id','=', lote.id if lote else False),\
                                                                 ])
            if linea_inventario_existente and producto_plantilla.tracking == "serial":
                #No podemos añadir la línea de inventario ya que el número de serie es único y ya existe una linea de ajuste
                #Marcamos el registro con 5
                self._marcar_registro_inventario(db_name, db_user, db_pass, db_host, db_table, 5, item['linea_id'])
            elif linea_inventario_existente:
                #Si el producto no tiene seguimiento o es por lotes, en lugar de generar una nueva linea, incrementamos la cantidad de la existente
                #Marcamos el registro con 2
                linea_inventario_existente.write({
                    'product_qty' : linea_inventario_existente.product_qty + float(item['product_qty'])
                })
                self._marcar_registro_inventario(db_name, db_user, db_pass, db_host, db_table, 2, item['linea_id'])                                                
            else:
                #Creamos la linea de inventario
                #Marcamos el registro con 1                                                        
                linea_inventario.create({
                    'inventory_id' : item['inventory_id'],
                    'location_id' : ubicacion.id if ubicacion else 8,
                    'product_id' : item['product_id'],
                    'prod_lot_id' : lote.id if lote else False,
                    'product_qty' : item['product_qty'],
                })                                               
                self._marcar_registro_inventario(db_name, db_user, db_pass, db_host, db_table, 1, item['linea_id'])
            
                
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

    def _create_query(self, db_table, offset=0, limit=100000, where='', order=''):
        query = "SELECT * FROM %s " % db_table
        if where:
            query += where

        query += " limit %s,%s " % (offset, limit)
        if order:
            query += " order %s" % order

        return query
    
    def _marcar_registro(self, db_name, db_user, db_pass, db_host, db_table, item):
        query = "UPDATE %s SET actualizado = 1 where idProducto = %s;" % (db_table, item)
        _logger.warning("Consulta %s " % query)
        self.execute(db_name, db_user, db_pass, db_host, query, commit=True)

    def _marcar_registro_inventario(self, db_name, db_user, db_pass, db_host, db_table, valor, item):
        query = "UPDATE %s SET actualizado = %s where linea_id = %s;" % (db_table, valor, item)
        _logger.warning("Consulta %s " % query)
        self.execute(db_name, db_user, db_pass, db_host, query, commit=True)