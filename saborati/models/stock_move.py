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
            
    @api.depends('bom_line_id')
    def _compute_description_bom_line(self):
        bom_line_description = {}
        for bom in self.bom_line_id.bom_id:
            if bom.type != 'phantom':
                continue
            line_ids = bom.bom_line_ids.ids
            total = len(line_ids)
            name = bom.display_name
            values = []
            for value in bom.product_id.product_template_variant_value_ids: 
                values.append(value.name)
                
            for i, line_id in enumerate(line_ids):
                bom_line_description[line_id] = '%s(%s) - %d/%d' % (name, ', '.join(values), i+1, total)

        for move in self:
            move.description_bom_line = bom_line_description.get(move.bom_line_id.id)