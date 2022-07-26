# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 

import logging 
_logger = logging.getLogger(__name__)


class Brand(models.Model): 
    _name = 'brand'
    _inherit = ['image.mixin']

    name = fields.Char('Name')
    product_ids = fields.One2many('product.template', 'brand')
