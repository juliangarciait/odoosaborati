# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 


class ExportCollectionToShopify(models.TransientModel): 
    _name = 'export.collection.to.shopify'
    
    instance_id = fields.Many2one('shopify.instance.ept', 'Instancia')
    
    def apply(self): 
        collections = self.env['product.collection'].search([('id', 'in', self._context['ids'])])
        
        shopify_product_collection_obj = self.env['shopify.product.collection']
        
        for collection in collections:
            for shopify_collection in collection.shopify_product_collection_ids: 
                if self.instance_id != shopify_collection.shopify_instance_id: 
                    shopify_product_collection_obj.create({
                        'name'                : collection.name, 
                        'collection_id'       : collection.id,
                        'body_html'           : collection.body_html, 
                        'company_id'          : self.instance_id.shopify_company_id.id,
                        'shopify_instance_id' : self.instance_id.id,
                        'image_1920'          : collection.image_1920,
                        'image_url'           : collection.image_url
                    })