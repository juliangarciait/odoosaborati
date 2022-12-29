# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError
from .. import shopify
from ..shopify.pyactiveresource.connection import ClientError
from ..shopify.pyactiveresource.connection import ResourceNotFound
import time
import base64

import logging
_logger = logging.getLogger(__name__)

class ProductCollection(models.Model): 
    _inherit = 'product.collection'
   
    @api.model
    def create(self, vals_list):
        res = super(ProductCollection, self).create(vals_list)

        shopify_product_collection_obj = self.env['shopify.product.collection']

        instances = self.env['shopify.instance.ept'].search([('shopify_company_id', '=', self.env.company.id)])
        for instance in instances: 
            shopify_product_collection_obj.create({
                'name'                : res.name, 
                'collection_id'       : res.id,
                'body_html'           : res.body_html, 
                'company_id'          : instance.shopify_company_id.id,
                'shopify_instance_id' : instance.id,
                'image_1920'          : res.image_1920,
                'image_url'           : res.image_url
            })

        return res

    def write(self, vals): 
        res = super(ProductCollection, self).write(vals)

        for collection in self:
            for shopify_collection in collection.shopify_product_collection_ids:
                shopify_collection.write({
                    'name'      : collection.name, 
                    'body_html' : collection.body_html,
                    'image_1920': collection.image_1920,
                    'image_url' : collection.image_url
                })
        return res
    
    def export_collections(self):
        return {
            'view_mode' : 'form', 
            'type'      : 'ir.actions.act_window', 
            'res_model' : 'export.collection.to.shopify', 
            'target'    : 'new', 
            'view_id'   : self.env.ref('shopify_ept.export_collection_to_shopify_wizard').id, 
            'context'   : {'ids' : self.env.context.get('active_ids', [])}
        }
        
                
    def update_collections_in_shopify(self):
        collections = self.env['product.collection'].search([('id', 'in', self.env.context.get('active_ids', []))])
        
        for collection in collections:
            for shopify_collection in collection.shopify_product_collection_ids:
                shopify_collection.write({
                    'name'      : collection.name, 
                    'body_html' : collection.body_html,
                    'image_1920': collection.image_1920,
                    'image_url' : collection.image_url
                })
                
                
    def unlink(self): 
        for collection in self: 
            for shopify_collection in collection.shopify_product_collection_ids: 
                shopify_collection.unlink()
                
        return super(ProductCollection, self).unlink()
            


class ShopifyProductCollection(models.Model):
    _inherit = 'shopify.product.collection'
    
    shopify_instance_id = fields.Many2one('shopify.instance.ept', string="Instance")
    
    @api.model
    def create(self, vals_list): 
        res = super(ShopifyProductCollection, self).create(vals_list)
        
        instance = res.shopify_instance_id
        
        instance.connect_in_shopify()
       
        new_collection = shopify.CustomCollection()

        new_collection.title           = res.name
        new_collection.body_html       = res.body_html
        #new_collection.image           = {"src" : res.image_url, 'alt' : "test"}
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
        res = super(ShopifyProductCollection, self).write(vals)
        
        for collection in self:
            collection.shopify_instance_id.connect_in_shopify()
            if collection.company_id.id == self.env.company.id:
                collect = self.request_collection(collection.shopify_collection_id)
                if collect: 
                    collect.title     = collection.name
                    collect.body_html = collection.body_html
                    #collect.image     = {"src" : collection.image_url}
                    
                    result = collect.save()
                    
                    if collection.is_exported: 
                        self.remove_products(collect)
                    
                    _logger.info('ANTESsssssssssssssSSsssS')
                    time.sleep(10)
                    _logger.info('DESPUESsssSSSSSSSSSss')
                    if collection.product_ids: 
                        self.add_products(collect, collection)
            else:
                new_collection = shopify.CustomCollection()

                new_collection.title           = collection.name
                new_collection.body_html       = collection.body_html
                #new_collection.image           = {"src" : collection.image_url}
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
            #else:
            #    raise ValidationError (_('No se puede editar esta collection porque no pertence a la compañía activa'))
                
        return res
    
    def add_products(self, collect, collection): 
        products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', collection.product_ids.ids)])
        n = 0
        for shopify_product in products:
            n += 1
            _logger.info(shopify_product.product_tmpl_id.name)
            _logger.info('$'*1000)
            new_product = shopify.Product().find(shopify_product.shopify_tmpl_id)
            collect.add_product(new_product)
            if n == 10:
                n = 0
                time.sleep(16)
    
    def update_collections_in_shopify(self):
        collections = self.env['shopify.product.collection'].search([('id', 'in', self.env.context.get('active_ids', []))])
        
        for collection in collections:
            if collection.company_id.id == self.env.company.id: 
                collection.shopify_instance_id.connect_in_shopify()
                if collection.is_exported:
                    self.export_collections(collection)
            else: 
                raise ValidationError ('Collection {} no pertenece la instancia de esta empresa'.format(collection))
                                    
    def remove_products(self, collect): 
        products = collect.products()
        n = 0 
        for product in products:
            n += 1
            dict_product = product.to_dict()
            current_product = shopify.Product().find(dict_product.get('id'))
            current_product.remove_from_collection(collect)
            if n == 10: 
                n = 0
                time.sleep(10)

    def request_collection(self, collection):
        try: 
            return shopify.CustomCollection().find(collection)
        except ClientError as error: 
            if hasattr(error, "response") and error.response.code == 429 and error.response.msg == "Too Many Requests": 
                time.sleep(int(float(error.response.headers.get('Retry-After', 5))))
                collect = shopify.CustomCollection().find(collection)
        except Exception as error: 
            _logger.info("Collection %s not found in shopify while updating it.\nError: %s" % (collection, str(error)))
            return False
        #if collect: 
        #    return collect
        #else: return False
    
    def unlink(self): 
        for collection in self: 
            collection.shopify_instance_id.connect_in_shopify()

            if collection.is_exported:
                _logger.info(collection.shopify_collection_id)
                collect = self.request_collection(collection.shopify_collection_id)
                if collect: 
                    collect.destroy()
        
        return super(ShopifyProductCollection, self).unlink()
    
    def remove_collections_in_shopify(self): 
        collections = self.env['product.collection'].search([('id', 'in', self.env.context.get('active_ids', []))])
        instances = self.env['shopify.instance.ept'].search([('shopify_company_id', '=', self.env.company.id)])
        
        for instance in instances: 
            instance.connect_in_shopify()
            for collection in collections.shopify_product_collection_ids:
                if collection.is_exported:
                    collect = self.request_collection(collection.shopify_collection_id)
                    if collect: 
                        collect.destroy()
                        collection.is_exported = False
                        
                        
    def export_collections(self, collection): 
        try: 
            collect = self.request_collection(collection.shopify_collection_id)
            if collect: 
                collect.title     = collection.name
                collect.body_html = collection.body_html
                
                result = collect.save()
                #collect.image     = {"attachment" : collection.image_1920.decode("utf-8")}
                
                if collection.is_exported: 
                    self.remove_products(collect)
                    
                if collection.product_ids: 
                    products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', collection.product_ids.ids)])
                    for shopify_product in products:
                        new_product = shopify.Product().find(shopify_product.shopify_tmpl_id)
                        collect.add_product(new_product)
        except ClientError as error: 
            if hasattr(error, "response") and error.response.code == 429 and error.response.msg == "Too Many Requests": 
                time.sleep(int(float(error.response.headers.get('Retry-After', 60))))
                collect = self.request_collection(collection.shopify_collection_id)
                if collect: 
                    collect.title     = collection.name
                    collect.body_html = collection.body_html
                    
                    result = collect.save()
                    #collect.image     = {"attachment" : collection.image_1920.decode("utf-8")}
                    
                    if collection.is_exported: 
                        self.remove_products(collect)
                        
                    if collection.product_ids: 
                        products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', collection.product_ids.ids)])
                        for shopify_product in products:
                            new_product = shopify.Product().find(shopify_product.shopify_tmpl_id)
                            collect.add_product(new_product)

    
    
                 
            
        


            

    