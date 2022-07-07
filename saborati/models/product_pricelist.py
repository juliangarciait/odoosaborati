# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging 
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model): 
    _inherit = 'product.pricelist.item'

    base = fields.Selection([('list_price', 'Sales Price'), ('replacement_cost', 'Replacement Cost'), ('pricelist', 'Other Pricelist')])