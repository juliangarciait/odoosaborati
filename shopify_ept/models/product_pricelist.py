# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import time
import logging 
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model): 
    _inherit = 'product.pricelist.item'

    def write(self, vals): 
        res = super(ProductPricelistItem, self).write(vals)
        for item in self: 
            self.with_delay(eta=5).update_prices_in_shopify(item)
                 
        return res

    @api.model
    def create(self, vals_list): 
        res = super(ProductPricelistItem, self).create(vals_list)

        self.with_delay(eta=5).update_prices_in_shopify(res)

        return res


    def unlink(self):
        for item in self: 
            if item.product_tmpl_id.shopify_product_template_ids and item.applied_on == '1_product': 
                item.product_tmpl_id.write({})
            elif item.applied_on == '0_product_variant' and item.product_id.product_tmpl_id.shopify_product_template_ids:
                item.product_id.product_tmpl_id.write({})
            elif item.applied_on == '2_product_category': 
                self.with_delay(eta=5).update_from_line_deleted(item)
        return super(ProductPricelistItem, self).unlink()
    
    def update_from_line_deleted(self, item): 
        product_ids = self.env['product.template'].search([('categ_id', '=', item.categ_id.id)])
        n = 0
        for product in product_ids:
            n += 1 
            product.write({})
            if n == 10: 
                n = 0
                time.sleep(5)
    
    
    def update_prices_in_shopify(self, item): 
        if item.product_tmpl_id.shopify_product_template_ids and item.applied_on == '1_product':
            for product in item.product_tmpl_id.shopify_product_template_ids: 
                export_data = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                    'shopify_is_set_basic_detail' : True,
                    'shopify_is_update_basic_detail' : True,
                    'shopify_is_set_price' : True,
                    'shopify_is_set_image' : True,
                    'shopify_is_publish' : 'publish_product_global',
                })
                export_data.with_context({"active_ids" : [product.id]}).manual_update_product_to_shopify()
        elif item.applied_on == '0_product_variant' and item.product_id.product_tmpl_id.shopify_product_template_ids:
            for product in item.product_id.product_tmpl_id.shopify_product_template_ids: 
                export_data = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                    'shopify_is_set_basic_detail' : True,
                    'shopify_is_update_basic_detail' : True,
                    'shopify_is_set_price' : True,
                    'shopify_is_set_image' : True,
                    'shopify_is_publish' : 'publish_product_global',
                })
                export_data.with_context({"active_ids" : [product.id]}).manual_update_product_to_shopify()
        elif item.applied_on == '2_product_category': 
            product_ids = self.env['product.template'].search([('categ_id', '=', item.categ_id.id)])
            n = 0
            for product in product_ids.shopify_product_template_ids: 
                n += 1
                export_data = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                    'shopify_is_set_basic_detail' : True,
                    'shopify_is_update_basic_detail' : True,
                    'shopify_is_set_price' : True,
                    'shopify_is_set_image' : True,
                    'shopify_is_publish' : 'publish_product_global',
                })
                export_data.with_context({"active_ids" : [product.id]}).manual_update_product_to_shopify()
                if n == 10: 
                    n = 0
                    time.sleep(5)
        