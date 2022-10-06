# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError
from .. import shopify
from ..shopify.pyactiveresource.connection import ClientError
from ..shopify.pyactiveresource.connection import ResourceNotFound
import time

import logging
_logger = logging.getLogger(__name__)

class ProductCollection(models.Model): 
    _inherit = 'product.collection'

    @api.model
    def create(self, vals_list):
        res = super(ProductCollection, self).create(vals_list)

        instance = self.env['shopify.instance.ept'].search([('shopify_company_id', '=', self.env.company.id)])
        instance.connect_in_shopify()

        new_collection = shopify.CustomCollection()

        new_collection.title           = res.name
        new_collection.body_html       = res.body_html
        new_collection.published_scope = "web"

        result = new_collection.save()

        if result: 
            collection_info = new_collection.to_dict()
            res.shopify_collection_id = collection_info.get('id')
            res.is_exported = True
            if res.product_ids: 
                products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', res.product_ids.ids)])
                for shopify_product in products:
                    new_product = shopify.Product().find(shopify_product.shopify_tmpl_id)
                    new_collection.add_product(new_product)
        elif not result: 
            raise ValidationError (_('Error al crear collection en Shopify'))

        return res

    def write(self, vals): 
        res = super(ProductCollection, self).write(vals)

        instance = self.env['shopify.instance.ept'].search([('shopify_company_id', '=', self.env.company.id)])
        instance.connect_in_shopify()

        for collection in self: 
            collect = self.request_collection(collection.shopify_collection_id)
            if collect: 
                collect.title     = collection.name
                collect.body_html = collection.body_html
                if collection.is_exported: 
                    self.remove_products(collect)
                    
                if collection.product_ids: 
                    products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', collection.product_ids.ids)])
                    for shopify_product in products:
                        new_product = shopify.Product().find(shopify_product.shopify_tmpl_id)
                        collect.add_product(new_product)
            else:
                new_collection = shopify.CustomCollection()

                new_collection.title           = collection.name
                new_collection.body_html       = collection.body_html
                new_collection.published_scope = "web"

                result = new_collection.save()
                
                if result: 
                    collection_info = new_collection.to_dict()
                    collection.shopify_collection_id = collection_info.get('id')
                    collection.is_exported = True
                    if collection.product_ids: 
                        products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', collection.product_ids.ids)])
                        for shopify_product in products:
                            new_product = shopify.Product().find(shopify_product.shopify_tmpl_id)
                            new_collection.add_product(new_product)
                elif not result: 
                    raise ValidationError (_('Error al crear collection en Shopify'))

        return res
    
    def remove_products(self, collect): 
        products = collect.products()
        
        for product in products: 
            dict_product = product.to_dict()
            current_product = shopify.Product().find(dict_product.get('id'))
            current_product.remove_from_collection(collect)

    def request_collection(self, collection): 
        try: 
            collect = shopify.CustomCollection().find(collection)
        except ClientError as error: 
            if hasattr(error, "response") and error.response.code == 429 and error.response.msg == "Too Many Requests": 
                time.sleep(int(float(error.response.headers.get('Retry-After', 5))))
                collect = shopify.CustomCollection().find(collection.shopify_collection_id)
        except Exception as error: 
            _logger.info("Collection %s not found in shopify while updating it.\nError: %s" % (collection.shopify_collection_id, str(error)))
            return False
        return collect
    
    def export_collections(self): 
        collections = self.env['product.collection'].search([('id', 'in', self.env.context.get('active_ids', []))])

        instance = self.env['shopify.instance.ept'].search([('shopify_company_id', '=', self.env.company.id)])
        instance.connect_in_shopify()
        
        for collection in collections:
            if not collection.is_exported: 
                new_collection = shopify.CustomCollection()
            
                new_collection.title           = collection.name
                new_collection.body_html       = collection.body_html
                new_collection.published_scope = "web"

                result = new_collection.save()

                if result: 
                    collection_info = new_collection.to_dict()
                    collection.shopify_collection_id = collection_info.get('id')
                    collection.is_exported = True
                    if collection.product_ids: 
                        products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', collection.product_ids.ids)])
                        for shopify_product in products:
                            new_product = shopify.Product().find(shopify_product.shopify_tmpl_id)
                            new_collection.add_product(new_product)
                elif not result: 
                    raise ValidationError (_('Error al crear collection en Shopify de la collection: {} - {}'.format(collection, collection.name)))
            
    def update_collections_in_shopify(self):
        collections = self.env['product.collection'].search([('id', 'in', self.env.context.get('active_ids', []))])
        
        instance = self.env['shopify.instance.ept'].search([('shopify_company_id', '=', self.env.company.id)])
        instance.connect_in_shopify()

        for collection in collections:
            if collection.is_exported:
                collect = self.request_collection(collection.shopify_collection_id)
                if collect: 
                    collect.title     = collection.name
                    collect.body_html = collection.body_html
                    self.remove_products(collect)
                        
                    if collection.product_ids: 
                        products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', collection.product_ids.ids)])
                        for shopify_product in products:
                            new_product = shopify.Product().find(shopify_product.shopify_tmpl_id)
                            collect.add_product(new_product)
            
                 
            
        


            

    