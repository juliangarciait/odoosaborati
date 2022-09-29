# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError
from .. import shopify
from ..shopify.pyactiveresource.connection import ClientError
from ..shopify.pyactiveresource.connection import ResourceNotFound

import logging
_logger = logging.getLogger(__name__)

class ProductCollection(models.Model): 
    _inherit = 'product.collection'

    @api.model
    def create(self, vals_list): 
        res = super(ProductCollection, self).create(vals_list)

        