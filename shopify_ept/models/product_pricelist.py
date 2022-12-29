# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging 
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model): 
    _inherit = 'product.pricelist.item'

    def write(self, vals): 
        res = super(ProductPricelistItem, self).write(vals)
        for item in self: 
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
                 
        return res

    @api.model
    def create(self, vals_list): 
        res = super(ProductPricelistItem, self).create(vals_list)

        if res.product_tmpl_id.shopify_product_template_ids:
                for product in res.product_tmpl_id.shopify_product_template_ids: 
                    export_data = self.env['shopify.process.import.export'].create({
                        'shopify_instance_id' : product.shopify_instance_id.id,
                        'shopify_is_set_basic_detail' : True,
                        'shopify_is_update_basic_detail' : True,
                        'shopify_is_set_price' : True,
                        'shopify_is_set_image' : True,
                        'shopify_is_publish' : 'publish_product_global',
                    })
                    export_data.with_context({"active_ids" : [product.id]}).manual_update_product_to_shopify()
                for product_variant in res.product_id.product_tmpl_id.shopify_product_template_ids:
                    export_data = self.env['shopify.process.import.export'].create({
                        'shopify_instance_id' : product_variant.shopify_instance_id.id,
                        'shopify_is_set_basic_detail' : True,
                        'shopify_is_update_basic_detail' : True,
                        'shopify_is_set_price' : True,
                        'shopify_is_set_image' : True,
                        'shopify_is_publish' : 'publish_product_global',
                    })
                    export_data.with_context({"active_ids" : [product_variant.id]}).manual_update_product_to_shopify()

        return res


    def unlink(self):
        for item in self: 
            if item.product_tmpl_id.shopify_product_template_ids and item.applied_on == '1_product': 
                for product in item.product_tmpl_id.shopify_product_template_ids: 
                    export_data = item.env['shopify.process.import.export'].create({
                            'shopify_instance_id' : product.shopify_instance_id.id,
                            'shopify_is_set_basic_detail' : False,
                            'shopify_is_update_basic_detail' : False,
                            'shopify_is_set_price' : True,
                            'shopify_is_set_image' : False,
                            'shopify_is_publish' : 'publish_product_web',
                        })
                    export_data.with_context({"active_ids" : [product.id]}).manual_update_product_to_shopify()
            elif item.applied_on == '0_product_variant' and item.product_id.product_tmpl_id.shopify_product_template_ids:
                for product in item.product_id.product_tmpl_id.shopify_product_template_ids: 
                    export_data = self.env['shopify.process.import.export'].create({
                        'shopify_instance_id' : product.shopify_instance_id.id,
                        'shopify_is_set_basic_detail' : False,
                        'shopify_is_update_basic_detail' : False,
                        'shopify_is_set_price' : True,
                        'shopify_is_set_image' : False,
                        'shopify_is_publish' : 'publish_product_web',
                    })
                    export_data.with_context({"active_ids" : [product.id]}).manual_update_product_to_shopify()
        return super(ProductPricelistItem, self).unlink()