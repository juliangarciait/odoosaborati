# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
from odoo.exceptions import ValidationError


class AssignMarginToProduct(models.Model): 
    _name = 'assign.margin.to.product'

    margin = fields.Float(string="Margen")


    def apply(self): 
        product_ids = self.env['product.template'].search([('id', 'in', self._context['ids'])])

        for product in product_ids: 
            self.env['product.margin'].create(
                {
                    'margin' : self.margin,
                    'product_tmpl_id' : product.id,
                }
            )
            self.with_delay().export_products(product)
    
    
    def export_products(self, product): 
        if product.detailed_type == 'product':
            for product_instance in product.shopify_product_template_ids:
                
                if not product.active: 
                    product_instance.product_status = 'archived'

                shopify_prepare_product_id = self.env['shopify.prepare.product.for.export.ept'].create({
                    'shopify_instance_id' : product_instance.shopify_instance_id.id, 
                    'export_method' : "direct",
                })
                export_data = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product_instance.shopify_instance_id.id,
                    'shopify_is_set_basic_detail' : True,
                    'shopify_is_update_basic_detail' : True,
                    'shopify_is_set_price' : True,
                    'shopify_is_set_image' : True,
                    'shopify_is_publish' : 'publish_product_global',
                })
                shopify_prepare_product_id.with_context({"active_ids": [product.id], "lang": self.env.user.lang}).prepare_product_for_export()
                if not product_instance.exported_in_shopify: 
                    export_data.with_context({"active_ids" : [product_instance.id]}).manual_export_product_to_shopify()
                else:
                    export_data.with_context({"active_ids" : [product_instance.id]}).manual_update_product_to_shopify()
