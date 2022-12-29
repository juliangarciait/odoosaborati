# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging 
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model): 
    _inherit = 'product.pricelist.item'

    base = fields.Selection([('list_price', 'Sales Price'), ('replacement_cost', 'Replacement Cost'), ('pricelist', 'Other Pricelist')])

    replacement_cost = fields.Char('Costo de reposición', compute="_compute_replacement_cost")
    
    @api.depends('applied_on')
    def _compute_replacement_cost(self):
        for item in self: 
            if item.applied_on == '1_product': 
                item.replacement_cost = str(item.product_tmpl_id.replacement_cost)
            elif item.applied_on == '0_product_variant': 
                item.replacement_cost = str(item.product_id.replacement_cost)
            else: 
                item.replacement_cost = 'No aplica'