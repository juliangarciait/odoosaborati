# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import base64
import logging
import io
from csv import DictWriter
from datetime import datetime
from io import StringIO

from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlsxwriter

_logger = logging.getLogger("Shopify Layer")


class PrepareProductForExport(models.TransientModel):
    """
    Model for adding Odoo products into Shopify Layer.
    @author: Maulik Barad on Date 11-Apr-2020.
    """
    _inherit = "shopify.prepare.product.for.export.ept"

    def export_direct_in_shopify(self, product_templates):
        """
        Creates new products or updates existing products in the Shopify layer using the direct export method.
        @author: Maulik Barad on Date 19-Sep-2020.
        """
        shopify_template_id = False
        sequence = 0
        variants = product_templates.product_variant_ids
        shopify_instance = self.shopify_instance_id

        for variant in variants:
            if not variant.default_code:
                continue
            product_template = variant.product_tmpl_id
            if product_template.attribute_line_ids and len(product_template.attribute_line_ids.filtered(
                    lambda x: x.attribute_id.create_variant == "always")) > 3:
                continue
            shopify_template, sequence, shopify_template_id = self.create_or_update_shopify_layer_template(
                shopify_instance, product_template, variant, shopify_template_id, sequence)

            self.create_shopify_template_images(shopify_template, variant)

            if shopify_template and shopify_template.shopify_product_ids and \
                    shopify_template.shopify_product_ids[0].sequence:
                sequence += 1

            shopify_variant = self.create_or_update_shopify_layer_variant(variant, shopify_template_id,
                                                                          shopify_instance, shopify_template, sequence)

            self.create_shopify_variant_images(shopify_template, shopify_variant)
        return True
    
    
    def prepare_template_val_for_export_product_in_layer(self, product_template, shopify_instance, variant):
        """ This method is used to prepare a template Vals for export/update product
            from Odoo products to the Shopify products layer.
            :param product_template: Record of odoo template.
            :param product_template: Record of instance.
            @return: template_vals
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 26 October 2020 .
            Task_id: 167537 - Code refactoring
        """
        ir_config_parameter_obj = self.env["ir.config_parameter"]
        template_vals = {"product_tmpl_id": product_template.id,
                         "shopify_instance_id": shopify_instance.id,
                         "shopify_product_category": product_template.categ_id.id,
                         "name": product_template.name,
                         "tag_ids": product_template.tag_ids.ids,
                         "replacement_cost": product_template.replacement_cost, 
                         "brand": product_template.brand.id,
                         }
        if ir_config_parameter_obj.sudo().get_param("shopify_ept.set_sales_description"):
            template_vals.update({"description": variant.description_sale})
        return template_vals
    
    
    def create_or_update_shopify_layer_variant(self, variant, shopify_template_id, shopify_instance,
                                               shopify_template, sequence):
        """ This method is used to create/update the variant in the shopify layer.
            @return: shopify_variant
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 26 October 2020 .
            Task_id: 167537 - Code refactoring
        """
        shopify_product_obj = self.env["shopify.product.product.ept"]
        shopify_variant = shopify_product_obj.search([
            ("shopify_instance_id", "=", self.shopify_instance_id.id),
            ("product_id", "=", variant.id),
            ("shopify_template_id", "=", shopify_template_id)])
        shopify_variant_vals = self.prepare_variant_val_for_export_product_in_layer(shopify_instance,
                                                                                    shopify_template, variant,
                                                                                    sequence)
        if not shopify_variant and variant.to_shopify:
            shopify_variant = shopify_product_obj.create(shopify_variant_vals)
        else:
            shopify_variant.write(shopify_variant_vals)
        return shopify_variant
    

    def create_shopify_template_images(self, shopify_template, variant):
        """
        For adding all odoo images into shopify layer only for template.
        @author: Maulik Barad on Date 19-Sep-2020.
        """
        shopify_product_image_list = []
        shopify_product_image_obj = self.env["shopify.product.image.ept"]
        product_template = shopify_template.product_tmpl_id
        for odoo_image in product_template.ept_image_ids.filtered(lambda x: not x.product_id):
            shopify_product_image = shopify_product_image_obj.search_read(
                [("shopify_template_id", "=", shopify_template.id),
                 ("odoo_image_id", "=", odoo_image.id)], ["id"])
            if not shopify_product_image and variant.to_shopify:
                shopify_product_image_list.append({
                    "odoo_image_id": odoo_image.id,
                    "shopify_template_id": shopify_template.id
                })
        if shopify_product_image_list:
            shopify_product_image_obj.create(shopify_product_image_list)
        return True
    

    def create_shopify_variant_images(self, shopify_template, shopify_variant):
        """
        For adding first odoo image into shopify layer for variant.
        @author: Maulik Barad on Date 19-Sep-2020.
        """
        shopify_product_image_obj = self.env["shopify.product.image.ept"]
        product_id = shopify_variant.product_id
        odoo_image = product_id.ept_image_ids
        if odoo_image:
            shopify_product_image = shopify_product_image_obj.search_read(
                [("shopify_template_id", "=", shopify_template.id),
                 ("shopify_variant_id", "=", shopify_variant.id),
                 ("odoo_image_id", "=", odoo_image[0].id)], ["id"])
            if not shopify_product_image and product_id.to_shopify:
                shopify_product_image_obj.create({
                    "odoo_image_id": odoo_image[0].id,
                    "shopify_variant_id": shopify_variant.id,
                    "shopify_template_id": shopify_template.id,
                    "sequence": 0
                })
        return True