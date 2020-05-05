# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import requests
import tempfile
import io
import zipfile
import os
import logging
import csv

logger = logging.getLogger(__name__)


class CityZipGeonamesImport(models.TransientModel):
    _inherit = 'city.zip.geonames.import'

    offset = fields.Integer('Desde')
    limit = fields.Integer('Cantidad')
    eliminar_antiguos = fields.Boolean('Eliminar antiguos')

    @api.model
    def get_and_parse_csv(self, country):
        parsed_csv = super(CityZipGeonamesImport, self).get_and_parse_csv(country)
        if self.limit:
            offset = self.offset if self.offset else 0
            parsed_csv = parsed_csv[offset:(self.limit + offset)]
        return parsed_csv

    def _process_csv(self, parsed_csv):
        state_model = self.env['res.country.state']
        zip_model = self.env['res.city.zip']
        res_city_model = self.env['res.city']
        # Store current record list
        old_zips = set(zip_model.search(
            [('city_id.country_id', '=', self.country_id.id)]).ids)
        search_zips = len(old_zips) > 0
        old_cities = set(res_city_model.search(
            [('country_id', '=', self.country_id.id)]).ids)
        search_cities = len(old_cities) > 0
        current_states = state_model.search(
            [('country_id', '=', self.country_id.id)])
        search_states = len(current_states) > 0
        max_import = self.env.context.get('max_import', 0)
        logger.info('Starting to create the cities and/or city zip entries')
        # Pre-create states and cities
        state_dict = self._create_states(parsed_csv,
                                         search_states, max_import)
        city_dict = self._create_cities(parsed_csv,
                                        search_cities, max_import, state_dict)
        # Zips
        zip_vals_list = []
        for i, row in enumerate(parsed_csv):
            if max_import and i == max_import:
                break
            # Don't search if there aren't any records
            zip_code = False
            state_id = state_dict[row[self.code_row_index or 4]]
            if search_zips:
                zip_code = self.select_zip(row, self.country_id, state_id)
            if not zip_code:
                city_id = city_dict[(
                    self.transform_city_name(row[2], self.country_id),
                    state_id,
                )]
                zip_vals = self.prepare_zip(row, city_id)
                if zip_vals not in zip_vals_list:
                    zip_vals_list.append(zip_vals)
            elif self.eliminar_antiguos:
                old_zips.remove(zip_code.id)
        self.env['res.city.zip'].create(zip_vals_list)
        if not max_import:
            if old_zips and self.eliminar_antiguos:
                logger.info('removing city zip entries')
                self.env['res.city.zip'].browse(list(old_zips)).unlink()
                logger.info('%d city zip entries deleted for country %s' %
                            (len(old_zips), self.country_id.name))
            old_cities -= set(city_dict.values())
            if old_cities and self.eliminar_antiguos:
                logger.info('removing city entries')
                self.env['res.city'].browse(list(old_cities)).unlink()
                logger.info('%d res.city entries deleted for country %s' %
                            (len(old_cities), self.country_id.name))
        logger.info(
            'The wizard to create cities and/or city zip entries from '
            'geonames has been successfully completed.')
        return True
