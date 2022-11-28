# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging 
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model): 
    _inherit = 'product.pricelist.item'

    base = fields.Selection([('list_price', 'Sales Price'), ('replacement_cost', 'Replacement Cost'), ('pricelist', 'Other Pricelist')])

    replacement_cost = fields.Char('Costo de reposición', compute="_compute_replacement_cost")
    
    @api.depends('applied_on')
    def _compute_replacement_cost(self):
        for item in self: 
            if item.applied_on == '1_product': 
                item.replacement_cost = str(item.product_tmpl_id.replacement_cost)
            elif item.applied_on == '0_product_variant': 
                item.replacement_cost = str(item.product_id.product_tmpl_id.replacement_cost)
            else: 
                item.replacement_cost = 'No aplica'
            

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

        return res


    def unlink(self):
        for item in self: 
            if item.product_tmpl_id.shopify_product_template_ids and item.applied_on == '1_product': 
                for product in item.product_tmpl_id.shopify_product_template_ids: 
                    export_data = item.env['shopify.process.import.export'].create({
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
        return super(ProductPricelistItem, self).unlink()