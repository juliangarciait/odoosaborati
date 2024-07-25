from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError
from ...shopify_ept import shopify
from ...shopify_ept.shopify.pyactiveresource.connection import ClientError
from ...shopify_ept.shopify.pyactiveresource.connection import ResourceNotFound
import time
import base64

import logging
_logger = logging.getLogger(__name__)

class ProductCollection(models.Model): 
    _name = 'product.collection'
    _inherit = ['image.mixin']

    name = fields.Char()
    body_html = fields.Html()
    is_exported = fields.Boolean()
    company_ids = fields.Many2many('res.company', string="Companies")
    shopify_product_collection_ids = fields.One2many('shopify.product.collection', 'collection_id', string="Shopify Product Collection")
    image_url = fields.Char()

    @api.model
    def get_image_ept(self, url, verify=False):
        image_types = ["image/jpeg", "image/png", "image/tiff",
                       "image/vnd.microsoft.icon", "image/x-icon",
                       "image/vnd.djvu", "image/svg+xml", "image/gif"]
        response = requests.get(url, stream=True, verify=verify, timeout=10)
        if response.status_code == 200 and response.headers["Content-Type"] in image_types:
            image = base64.b64encode(response.content)
            if image:
                return image
        raise UserError(_("Can't find image.\nPlease provide valid Image URL."))
   
    @api.model
    def create(self, vals_list):
        verify = False
        ir_config_parameter_obj = self.env['ir.config_parameter']
        if not vals_list.get("image_1920", False) and vals_list.get("image_url", ""):
            if 'ssl_verify' in list(self.env.context.keys()):
                verify = True
            image = self.get_image_ept(vals_list.get("image_url"), verify=verify)
            vals_list.update({"image_1920": image})
        res = super(ProductCollection, self).create(vals_list)

        base_url = ir_config_parameter_obj.sudo().get_param('web.base.url')
        rec_id = str(res.id)
        url = base_url + '/cl/i/%s' % (base64.urlsafe_b64encode(rec_id.encode("utf-8")).decode("utf-8"))
        res.write({'image_url': url})

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
    _name = 'shopify.product.collection'
    _inherit = ['image.mixin']

    name = fields.Char()
    body_html = fields.Html()
    is_exported = fields.Boolean()

    company_id = fields.Many2one('res.company', string="Company")
    product_ids = fields.Many2many('product.template', string="Products")
    shopify_collection_id = fields.Char("Shopify Collection ID")
    image_url = fields.Char()
    
    collection_id = fields.Many2one('product.collection', company_dependent=True)
    
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
        elif not result: 
            raise ValidationError (_('Error al crear collection en Shopify'))

        return res
        
    def write(self, vals): 
        res = super(ShopifyProductCollection, self).write(vals)
        
        for collection in self:
            self.with_delay(eta=5).export_to_shopify(collection)
             
        return res
    
    def export_to_shopify(self, collection): 
        collection.shopify_instance_id.connect_in_shopify()
        collect = self.request_collection(collection.shopify_collection_id)
        if collect: 
            collect.title     = collection.name
            collect.body_html = collection.body_html
            #collect.image     = {"src" : collection.image_url}
            
            result = collect.save()
            
            if collection.is_exported: 
                self.remove_products(collect, collection)
            
            if collection.product_ids:
                time.sleep(10)
                self.add_products(collect, collection)
        #else:
        #    raise ValidationError (_('No se puede editar esta collection porque no pertence a la compañía activa'))
    
    def add_products(self, collect, collection): 
        products = self.env['shopify.product.template.ept'].search([('product_tmpl_id', 'in', collection.product_ids.ids)])
        n = 0
        for shopify_product in products:
            new_product = self.request_product(shopify_product.shopify_tmpl_id)
            if new_product: 
                n += 1
                collect.add_product(new_product)
            
            if n == 10: 
                n = 0
                time.sleep(5)

            
    def request_product(self, shopify_tmpl_id): 
        try: 
            return shopify.Product().find(shopify_tmpl_id)
        except ClientError as error: 
            if hasattr(error, "response") and error.response.code == 429 and error.response.msg == "Too Many Requests": 
                time.sleep(int(float(error.response.headers.get('Retry-After', 5))))
                return shopify.Product().find(shopify_tmpl_id)
        except Exception as error: 
            _logger.info("Product %s not found in shopify while updating collection.\nError: %s" % (shopify_tmpl_id, str(error)))
            return False
    
    def update_collections_in_shopify(self):
        collections = self.env['shopify.product.collection'].search([('id', 'in', self.env.context.get('active_ids', []))])
        
        for collection in collections:
            self.with_delay(eta=5).export_to_shopify(collection)
                                    
    def remove_products(self, collect, collection): 
        products = collect.products()
        n = 0
        for product in products:
            n += 1
            collect.remove_product(product)
            if n == 10: 
                n = 0 
                time.sleep(5)
        #for product in products
            #dict_product = product.to_dict()
            #current_product = shopify.Product().find(dict_product.get('id'))
            #collect.remove_product(current_product)
            #if n == 10: 
            #    n = 0
            #    time.sleep(5)

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


