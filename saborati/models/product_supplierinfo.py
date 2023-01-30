# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
import logging
_logger = logging.getLogger(__name__)

class ProductSupplierinfo(models.Model): 
    _inherit = 'product.supplierinfo'
    
    @api.model
    def create(self, vals_list):
        res = super(ProductSupplierinfo, self).create(vals_list)
        
        self.with_delay().update_prices_in_shopify(res.product_tmpl_id)
        
        return res
    
    def write(self, vals): 
        res = super(ProductSupplierinfo, self).write(vals)
        
        for vendor_pricelist in self: 
            self.with_delay().update_prices_in_shopify(vendor_pricelist.product_tmpl_id)
        
        return res
    
    def unlink(self): 
        for vendor_pricelist in self: 
            self.with_delay().update_prices_in_shopify(vendor_pricelist.product_tmpl_id)
            
        return super(ProductSupplierinfo, self).unlink()
    
    def update_prices_in_shopify(self, product_tmpl_id): 
        bom_ids = self.env['mrp.bom.line'].search([('product_id.product_tmpl_id', '=', product_tmpl_id.id)]).bom_id
        for bom in bom_ids: 
            for product in bom.product_tmpl_id.shopify_product_template_ids: 
                export_data = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                    'shopify_is_set_basic_detail' : True,
                    'shopify_is_update_basic_detail' : True,
                    'shopify_is_set_price' : True,
                    'shopify_is_set_image' : False,
                    'shopify_is_publish' : 'publish_product_global',
                })
                if product.exported_in_shopify:
                    export_data.with_context({"active_ids" : [product.id], "lang": self.env.user.lang}).manual_update_product_to_shopify()
        
        
        