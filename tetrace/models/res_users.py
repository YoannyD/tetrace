# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, modules

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = "res.users"

    validacion_user_ids = fields.One2many('tetrace.validacion_user', 'user_id')
    rango_validaciones = fields.Integer("Rango", default= 6)
    sale_order_coordinador_ids = fields.One2many("sale.order", "coordinador_proyecto_id")
    
    @api.model
    def review_user_count(self):
        user_reviews = {}
        to_review_docs = {}
        reviews = self.env["tier.review"].search(
            [
                ("status", "=", "pending"),
                ("can_review", "=", True),
                ("id", "in", self.env.user.review_ids.ids),
            ]
        )
        for review in reviews:
            _logger.warning(review)
            record = (
                review.env[review.model]
#                 .with_user(self.env.user)
                .search([("id", "=", review.res_id)])
            )
            _logger.warning("===========")
            _logger.warning(record)
            _logger.warning(record.rejected)
            _logger.warning(record.can_review)
            _logger.warning("===========")
            if not record or record.rejected or not record.can_review:
                # Checking that the review is accessible with the permissions
                # and to review condition is valid
                continue
            if not user_reviews.get(review["model"]):
                user_reviews[review.model] = {
                    "name": record._description,
                    "model": review.model,
                    "icon": modules.module.get_module_icon(
                        self.env[review.model]._original_module
                    ),
                    "pending_count": 0,
                }
            docs = to_review_docs.get(review.model)
            _logger.warning(record)
            _logger.warning(docs)
            if (docs and record not in docs) or not docs:
                _logger.warning("mas 1111111111")
                user_reviews[review.model]["pending_count"] += 1
            to_review_docs.setdefault(review.model, []).append(record)
            
        
        return list(user_reviews.values())
    
    @api.model
    def get_reviews(self, data):
        _logger.warning("get_reviews")
        _logger.warning(data)
        review_obj = self.env["tier.review"].with_context(lang=self.env.user.lang)
        res = review_obj.search_read([("id", "in", data.get("res_ids"))])
        for r in res:
            # Get the translated status value.
            r["display_status"] = dict(
                review_obj.fields_get("status")["status"]["selection"]
            ).get(r.get("status"))
            # Convert to datetime timezone
            if r["reviewed_date"]:
                r["reviewed_date"] = fields.Datetime.context_timestamp(
                    self, r["reviewed_date"]
                )
        return res