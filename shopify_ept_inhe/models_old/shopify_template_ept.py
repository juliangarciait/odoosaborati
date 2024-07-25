import base64
import hashlib
import json
import logging
import time
from datetime import datetime
import requests
from dateutil import parser
import pytz

from odoo import models, fields, api
from ...shopify_ept import shopify
from ...shopify_ept.shopify.pyactiveresource.connection import ClientError

utc = pytz.utc
_logger = logging.getLogger("Shopify Template")


class ShopifyProductTemplateEpt(models.Model):
    _inherit = "shopify.product.template.ept"

    tag_ids = fields.Many2many("product.tags", string="Tags")
    brand = fields.Many2one("brand", string="Brand*")
    replacement_cost = fields.Float("Replacement Cost")
    product_status = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('archived', 'Archived')], default="draft", string="Product status")

    def cron_update_products_in_shopify(self): 
        products = self.search([])

        for product in products: 
            if product.exported_in_shopify:
                export_data = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id'            : product.shopify_instance_id.id,
                    'shopify_is_set_basic_detail'    : True,
                    'shopify_is_update_basic_detail' : True,
                    'shopify_is_set_price'           : True,
                    'shopify_is_set_image'           : True,
                    'shopify_is_publish'             : 'publish_product_global',
                })
                export_data.with_context({"active_ids" : [product.id]}).manual_update_product_to_shopify()

    def cron_update_stock(self):
        for product in self.search([]): 
            process_import_export_obj = False
            process_import_export_obj = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : product.shopify_instance_id.id,
            })

            if process_import_export_obj: 
                process_import_export_obj.with_context({'active_ids' : [product.id]}).with_delay(eta=5).shopify_selective_product_stock_export()

    def update_from_form(self): 
        export_data = self.env['shopify.process.import.export'].create({
            'shopify_instance_id' : self.shopify_instance_id.id,
            'shopify_is_set_basic_detail' : True,
            'shopify_is_update_basic_detail' : True,
            'shopify_is_set_price' : True,
            'shopify_is_set_image' : True,
            'shopify_is_publish' : 'publish_product_global',
        })
        if self.exported_in_shopify:
            export_data.with_context({"active_ids" : [self.id], "lang": self.env.user.lang}).manual_update_product_to_shopify()
            self.product_tmpl_id.sudo().with_delay(eta=5).export_collections(self.product_tmpl_id, self)

        process_import_export_obj = self.env['shopify.process.import.export'].create({
            'shopify_instance_id' : self.shopify_instance_id.id,
        })
        if process_import_export_obj: 
            process_import_export_obj.with_context({'active_ids' : [self.id]}).sudo().shopify_selective_product_stock_export()


    def create_or_update_shopify_template(self, template_dict, variant_length, shopify_template, odoo_product=False,
                                          odoo_template=False):
        vals = {
            "shopify_instance_id": template_dict.get("shopify_instance_id"),
            "name": template_dict.get("template_title"),
            "shopify_tmpl_id": template_dict.get("shopify_tmpl_id"),
            "created_at": template_dict.get("created_at"),
            "updated_at": template_dict.get("updated_at"),
            "description": template_dict.get("body_html"),
            "published_at": template_dict.get("published_at"),
            "website_published": template_dict.get("website_published"),
            "exported_in_shopify": True,
            "total_variants_in_shopify": variant_length,
            "shopify_product_category": template_dict.get("shopify_product_category"),
            "tag_ids": [(6, 0, template_dict.get("tags"))]
            }

        if shopify_template:
            shopify_template.write(vals)
        else:
            if odoo_product:
                vals.update({"product_tmpl_id": odoo_product.product_tmpl_id.id})
            elif odoo_template:
                vals.update({'product_tmpl_id': odoo_template.id})
            shopify_template = self.create(vals)

        return shopify_template
    

    def change_product_status(self): 
        return {
            'view_mode' : 'form', 
            'type' : 'ir.actions.act_window', 
            'res_model' : 'change.product.status', 
            'target' : 'new', 
            'view_id' : self.env.ref('shopify_ept.change_product_status_view').id,
            'context' : {'ids' : self.env.context.get('active_ids', [])}
        }