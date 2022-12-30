# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 

import logging

_logger = logging.getLogger(__name__)

class StockQuant(models.Model): 
    _inherit = 'stock.quant'
    
    def action_apply_inventory(self):
        res = super(StockQuant, self).action_apply_inventory()
        
        for product in self.product_id.product_tmpl_id.shopify_product_template_ids:
            
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : product.shopify_instance_id.id,
                
            })
            process_import_export_obj.with_context({'active_ids' : [product.id]}).shopify_selective_product_stock_export()

        return res        
        