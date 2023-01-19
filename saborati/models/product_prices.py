# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 

import logging
_logger = logging.getLogger(__name__)

class ProductPrices(models.Model): 
    _name = 'product.prices'
    
    product_pricelist_id = fields.Many2one('product.pricelist', 'Lista de precios')
    price = fields.Char('Precio', readonly="1", store=True, compute='_compute_product_pricelist')
    product_tmpl_id = fields.Many2one('product.template', 'Product')
    
    @api.depends('product_pricelist_id', 'product_pricelist_id.item_ids')
    def _compute_product_pricelist(self): 
        for record in self: 
            if record.product_pricelist_id:
                price = record.product_pricelist_id.get_product_price(record.product_tmpl_id.product_variant_id, 1.0, partner=False, uom_id=record.product_tmpl_id.product_variant_id.uom_id.id)
                price_with_tax = record.product_tmpl_id.taxes_id.compute_all(float(price), product=record.product_tmpl_id, partner=self.env['res.partner']) 
                record.price = str(float(price)) + " (" + str(float(price_with_tax['total_included'])) + " con impuestos)"   