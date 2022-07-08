# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class ProductMargin(models.Model): 
    _name = 'product.margin'

    margin = fields.Float('Margin')
    product_tmpl_id = fields.Many2one('product.template')

    @api.model
    def create(self, vals_list): 
        margin = super(ProductMargin, self).create(vals_list)

        margin.product_tmpl_id.list_price = margin.product_tmpl_id.replacement_cost / (1 - margin.margin)

        return margin 