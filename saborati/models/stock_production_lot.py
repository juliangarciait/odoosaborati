# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 

import logging

_logger = logging.getLogger(__name__)

class StockProductionLot(models.Model): 
    _inherit = 'stock.production.lot'
    
    @api.model
    def create(self, vals_list): 
        res = super(StockProductionLot, self).create(vals_list)
        
        process_import_export_obj = False
        for product in res.product_id.product_tmpl_id.shopify_product_template_ids:
            
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : product.shopify_instance_id.id,
            })
            
            if process_import_export_obj: 
                process_import_export_obj.with_context({'active_ids' : [product.id]}).shopify_selective_product_stock_export()
        
        return res
    
    def write(self, vals): 
        res = super(StockProductionLot, self).write(vals)
        
        process_import_export_obj = False
        for product in self.product_id.product_tmpl_id.shopify_product_template_ids:
            
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : product.shopify_instance_id.id,
            })
            
            if process_import_export_obj: 
                process_import_export_obj.with_context({'active_ids' : [product.id]}).shopify_selective_product_stock_export()
        
        return res