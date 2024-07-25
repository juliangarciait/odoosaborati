# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import base64
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging 
_logger = logging.getLogger(__name__)


class ProductImageEpt(models.Model):
    _inherit = 'common.product.image.ept'

    def create(self, vals):
        record = super(ProductImageEpt, self).create(vals)
        print("aqui correr la actualizacion")
        return record
    
    def write(self, vals):
        record = super(ProductImageEpt, self).write(vals)
        print("aqui correr la actualizacion")
        return record