# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model): 
    _inherit = 'product.template'

    margin_ids = fields.One2many('product.margin', 'product_tmpl_id')
