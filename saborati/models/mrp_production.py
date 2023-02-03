# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 

import logging 
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model): 
    _inherit = 'mrp.production'
    
    def button_mark_done(self): 
        res = super(MrpProduction, self).button_mark_done()
        
        products = self.product_id.product_tmpl_id.shopify_product_template_ids.ids
        for line in self.move_raw_ids: 
            for product in line.product_id.product_tmpl_id.shopify_product_template_ids: 
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                })
                products.append(product.id)
                
        if process_import_export_obj: 
            process_import_export_obj.with_context({'active_ids' : products}).shopify_selective_product_stock_export()
        
        return res
    
    def button_scrap(self): 
        res = super(MrpProduction, self).button_scrap()
        
        products = self.product_id.product_tmpl_id.shopify_product_template_ids.ids
        for line in self.move_raw_ids: 
            for product in line.product_id.product_tmpl_id.shopify_product_template_ids: 
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                })
                products.append(product.id)
                
        if process_import_export_obj: 
            process_import_export_obj.with_context({'active_ids' : products}).shopify_selective_product_stock_export()
        
        return res
    
    def button_unbuild(self): 
        res = super(MrpProduction, self).button_unbuild()
        
        products = self.product_id.product_tmpl_id.shopify_product_template_ids.ids
        for line in self.move_raw_ids: 
            for product in line.product_id.product_tmpl_id.shopify_product_template_ids: 
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                })
                products.append(product.id)
                
        if process_import_export_obj: 
            process_import_export_obj.with_context({'active_ids' : products}).shopify_selective_product_stock_export()
        
        return res