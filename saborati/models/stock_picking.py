# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 

import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model): 
    _inherit = 'stock.picking'
    
    def button_validate(self): 
        res = super(StockPicking, self).button_validate()
        products = []
        for line in self.move_ids_without_package: 
            for product in line.product_id.product_tmpl_id.shopify_product_template_ids: 
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                })
                products.append(product.id)
        
        process_import_export_obj.with_context({'active_ids' : products}).shopify_selective_product_stock_export()
        
        return res
    
class StockReturnPicking(models.TransientModel): 
    _inherit = 'stock.return.picking'
    
    def create_returns(self): 
        res = super(StockReturnPicking, self).create_returns()
        products = []
        for line in self.product_return_moves: 
            for product in line.product_id.product_tmpl_id.shopify_product_template_ids: 
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                })
                products.append(product.id)
        
        process_import_export_obj.with_context({'active_ids' : products}).shopify_selective_product_stock_export()
            
        
        return res