# -*- coding: utf-8 -*-

from odoo import fields, api, _, models

import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    select_product_ids = fields.Many2many('product.product', compute="_get_products")
    
    @api.depends('picking_id.sale_id.order_line')
    def _get_products(self): 
        products = []
        for record in self: 
            if record.picking_id.sale_id: 
                _logger.info(record.picking_id.sale_id)
                _logger.info('%'*10)
                for line in record.picking_id.sale_id.order_line: 
                    _logger.info(line.product_id)
                    products.append(line.product_id.id)
            record.select_product_ids = products
            _logger.info(record.select_product_ids)
            _logger.info('$'*1000)