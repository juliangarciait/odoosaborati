# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from .. import shopify
import time
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    description_sale = fields.Html()

    shopify_product_template_ids = fields.One2many('shopify.product.template.ept', 'product_tmpl_id')

    product_status_colors = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('archived', 'Archived')], compute='_compute_product_status')

    @api.depends('shopify_product_template_ids.product_status')
    def _compute_product_status(self): 
        for record in self: 
            record.product_status_colors = False
            if record.shopify_product_template_ids: 
                for template in record.shopify_product_template_ids:
                    record.product_status_colors = template.product_status
                    
    #@api.model
    #def create(self, vals_list): 
    #    res = super(ProductTemplate, self).create(vals_list)
        
    #    if res.detailed_type == 'product' and not res.shopify_product_template_ids and res.default_code: 
    #        instance = self.env['shopify.instance.ept'].search([('shopify_company_id', '=', self.env.company.id)])
    #        export_data = self.env['shopify.process.import.export'].create({
    #            'shopify_instance_id' : instance.id,
    #            'shopify_is_set_basic_detail' : True,
    #            'shopify_is_update_basic_detail' : True,
    #            'shopify_is_set_price' : True,
    #            'shopify_is_set_image' : True,
    #            'shopify_is_publish' : 'publish_product_global',
    #        })
            
    #        shopify_prepare_product_id = self.env['shopify.prepare.product.for.export.ept'].create({
    #            'shopify_instance_id' : instance.id, 
    #            'export_method' : "direct",
    #        })
    #        shopify_prepare_product_id.with_context({"active_ids": [res.id], "lang": self.env.user.lang}).prepare_product_for_export()
    #        product_instance = self.env['shopify.product.template.ept'].search([('product_tmpl_id', '=', res.id)])
    #        export_data.with_context({"active_ids" : [product_instance.id]}).manual_export_product_to_shopify()
    #    elif res.detailed_type == 'product' and not res.shopify_product_template_ids and not res.default_code: 
    #        raise ValidationError ('El producto no tiene referencia interna, por favor coloque una antes de guardarlo')
        
    #    return res

    def write(self, vals):
        """
        This method use to archive/unarchive shopify product templates base on odoo product templates.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 09/12/2019.
        :Task id: 158502
        """
        #if 'active' in vals.keys():
        #    shopify_product_template_obj = self.env['shopify.product.template.ept']
        #    for template in self:
        #        shopify_templates = shopify_product_template_obj.search(
        #            [('product_tmpl_id', '=', template.id)])
        #        if vals.get('active'):
        #           shopify_templates = shopify_product_template_obj.search(
        #                [('product_tmpl_id', '=', template.id), ('active', '=', False)])
        #        shopify_templates.write({'active': vals.get('active')})
        
        res = super(ProductTemplate, self).write(vals)

        for product in self:
            if product.detailed_type == 'product':
                self.with_delay().export_to_shopify(product)
                            
                            #if product_collection.shopify_instance_id == product_instance.shopify_instance_id: 
                                           
                                            
                                           
                #else: 
                #    shopify_prepare_product_id = self.env['shopify.prepare.product.for.export.ept'].create({
                #        'shopify_instance_id' : instance.id, 
                #        'export_method' : "direct",
                #    })
                #    shopify_prepare_product_id.with_context({"active_ids": [product.id], "lang": self.env.user.lang}).prepare_product_for_export()
                #    product_instance = self.env['shopify.product.template.ept'].search([('product_tmpl_id', '=', product.id)])
                #    export_data.with_context({"active_ids" : [product_instance.id]}).manual_export_product_to_shopify()
                    

            shopify_templates = self.env['shopify.product.template.ept'].search(
                        [('product_tmpl_id', '=', product.id)])
            if product.active:
                shopify_templates = self.env['shopify.product.template.ept'].search(
                    [('product_tmpl_id', '=', product.id), ('active', '=', False)])
            shopify_templates.write({'active': product.active})

        shopify_product = self.env['shopify.product.product.ept'].search(
                    [('product_id', '=', product.product_variant_id.id)])
        if vals.get('active'):
            shopify_product = self.env['shopify.product.product.ept'].search(
                [('product_id', '=', product.product_variant_id.id), ('active', '=', False)])
        shopify_product.write({'active': product.product_variant_id.active})
            
        return res
    
    
    def export_to_shopify(self, product):
        for product_instance in product.shopify_product_template_ids:
            export_data = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : product_instance.shopify_instance_id.id,
                'shopify_is_set_basic_detail' : True,
                'shopify_is_update_basic_detail' : True,
                'shopify_is_set_price' : True,
                'shopify_is_set_image' : True,
                'shopify_is_publish' : 'publish_product_global',
            })
            
            if not product.active: 
                product_instance.product_status = 'archived'
                
            shopify_prepare_product_id = self.env['shopify.prepare.product.for.export.ept'].create({
                'shopify_instance_id' : product_instance.shopify_instance_id.id, 
                'export_method' : "direct",
            })
            shopify_prepare_product_id.with_context({"active_ids": [product.id], "lang": self.env.user.lang}).prepare_product_for_export()
            if product_instance.exported_in_shopify:
                export_data.with_context({"active_ids" : [product_instance.id], "lang": self.env.user.lang}).manual_update_product_to_shopify()
                
            #Add to collection if it has collections
            if product.product_collection_ids: 
                for product_collection in product.product_collection_ids: 
                    product_collection.shopify_instance_id.connect_in_shopify()
                    if product_collection.shopify_instance_id == product_instance.shopify_instance_id: 
                        shopify_product = shopify.Product().find(product_instance.shopify_tmpl_id)
                        collections = shopify_product.collections()
                        if collections:
                            for collect in collections: 
                                shopify_product.remove_from_collection(collect)
                                
                for product_collection in product.product_collection_ids:
                    product_collection.shopify_instance_id.connect_in_shopify()     
                    if product_collection.is_exported and product_collection.company_id.id == self.env.company.id and product_collection.shopify_instance_id == product_instance.shopify_instance_id:
                        collect = product_collection.request_collection(product_collection.shopify_collection_id)
                        if collect:
                            shopify_product.add_to_collection(collect) 
                            
        return True
        

                    
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    shopify_product_ids = fields.One2many('shopify.product.product.ept', 'product_id')
    
    def delete_variants_in_shopify(self, shopify_product_tmpl, shopify_product_variant): 
        for variant in shopify_product_tmpl.variants: 
            product_dict = variant.to_dict()
            if str(product_dict.get('id')) == str(shopify_product_variant.variant_id): 
                variant.destroy()
                _logger.info(shopify_product_variant.exported_in_shopify)
                
    def export_deleted_variant(self, shopify_product_variant): 
        shopify_product_variant.unlink()

    
    
    def export_variant_to_shopify(self, product_variant):
        if product_variant.shopify_product_ids: 
            for shopify_product_variant in product_variant.shopify_product_ids: 
                shopify_product_variant.shopify_instance_id.connect_in_shopify() 
                if not shopify_product_variant.to_shopify: 
                    shopify_product_tmpl = shopify.Product().find(shopify_product_variant.shopify_template_id.shopify_tmpl_id)
                    if shopify_product_tmpl.variants: 
                        self.delete_variants_in_shopify(shopify_product_tmpl, shopify_product_variant)
                    else: 
                        raise ValidationError('Las variantes no están exportadas en Shopify.')
                    shopify_product_variant.exported_in_shopify = False
                    self.export_deleted_variant(shopify_product_variant)
                        
        for product in product_variant.product_tmpl_id: 
            if product.detailed_type == 'product':
                for product_instance in product.shopify_product_template_ids:
                    export_data = self.env['shopify.process.import.export'].create({
                        'shopify_instance_id' : product_instance.shopify_instance_id.id,
                        'shopify_is_set_basic_detail' : True,
                        'shopify_is_update_basic_detail' : True,
                        'shopify_is_set_price' : True,
                        'shopify_is_set_image' : True,
                        'shopify_is_publish' : 'publish_product_global',
                    })
                    
                    if not product.active: 
                        product_instance.product_status = 'archived'
                        
                    shopify_prepare_product_id = self.env['shopify.prepare.product.for.export.ept'].create({
                        'shopify_instance_id' : product_instance.shopify_instance_id.id, 
                        'export_method' : "direct",
                    })
                    shopify_prepare_product_id.with_context({"active_ids": [product.id], "lang": self.env.user.lang}).prepare_product_for_export()
                    if product_instance.exported_in_shopify:
                        export_data.with_context({"active_ids" : [product_instance.id], "lang": self.env.user.lang}).manual_update_product_to_shopify()
                        
        return True
                        

    def write(self, vals):
        """
        This method use to archive/unarchive shopify product base on odoo product.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 30/03/2019.
        """
        #if 'active' in vals.keys():
        #    shopify_product_product_obj = self.env['shopify.product.product.ept']
        #    for product in self:
        #        shopify_product = shopify_product_product_obj.search(
        #            [('product_id', '=', product.id)])
        #        if vals.get('active'):
        #            shopify_product = shopify_product_product_obj.search(
        #                [('product_id', '=', product.id), ('active', '=', False)])
        #        shopify_product.write({'active': vals.get('active')})
        res = super(ProductProduct, self).write(vals)
        
        for product_variant in self: 
            self.with_delay().export_variant_to_shopify(product_variant)
            
            
        return res
    
    def export_new_variant_to_shopify(self): 
        variant_ids = self.env['product.product'].search([('id', 'in', self.env.context.get('active_ids', []))])
        
        self.export_new_variant(variant_ids)
        
        return {}
        
    def export_new_variant(self, variant_ids): 
        for variant in variant_ids: 
            for product in variant.product_tmpl_id: 
                if product.detailed_type == 'product':
                    for product_instance in product.shopify_product_template_ids:
                        export_data = self.env['shopify.process.import.export'].create({
                            'shopify_instance_id' : product_instance.shopify_instance_id.id,
                            'shopify_is_set_basic_detail' : True,
                            'shopify_is_update_basic_detail' : True,
                            'shopify_is_set_price' : True,
                            'shopify_is_set_image' : True,
                            'shopify_is_publish' : 'publish_product_global',
                        })
                        
                        if not product.active: 
                            product_instance.product_status = 'archived'
                            
                        shopify_prepare_product_id = self.env['shopify.prepare.product.for.export.ept'].create({
                            'shopify_instance_id' : product_instance.shopify_instance_id.id, 
                            'export_method' : "direct",
                        })
                        shopify_prepare_product_id.with_context({"active_ids": [product.id], "lang": self.env.user.lang}).prepare_product_for_export()
                        if product_instance.exported_in_shopify:
                            export_data.with_context({"active_ids" : [product_instance.id], "lang": self.env.user.lang}).manual_update_product_to_shopify()
                    
