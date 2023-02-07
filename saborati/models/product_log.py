# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 

import logging 
_logger = logging.getLogger(__name__)

class ProductLog(models.Model):
    _name = 'product.log'
    
    product_id = fields.Many2one('product.product')
    instance_id = fields.Many2one('shopify.instance.ept')