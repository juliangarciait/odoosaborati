# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import json
import logging

from calendar import monthrange
from datetime import date, datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ...shopify_ept import shopify
from ...shopify_ept.shopify.pyactiveresource.connection import ForbiddenAccess

_logger = logging.getLogger("Shopify Instance")
_secondsConverter = {
    'days': lambda interval: interval * 24 * 60 * 60,
    'hours': lambda interval: interval * 60 * 60,
    'weeks': lambda interval: interval * 7 * 24 * 60 * 60,
    'minutes': lambda interval: interval * 60,
}


class ShopifyInstanceEpt(models.Model):
    _inherit = "shopify.instance.ept"

    shopify_b2b_pricelist_id = fields.Many2one('product.pricelist', string='B2B Pricelist')
    shopify_wholesale_pricelist_id = fields.Many2one('product.pricelist', string='Wholesale Pricelist')
    shopify_medium_id = fields.Many2one('utm.medium', string="Medio")