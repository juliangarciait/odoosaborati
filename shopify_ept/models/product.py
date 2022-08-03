# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        """
        This method use to archive/unarchive shopify product templates base on odoo product templates.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 09/12/2019.
        :Task id: 158502
        """
        if 'active' in vals.keys():
            shopify_product_template_obj = self.env['shopify.product.template.ept']
            for template in self:
                shopify_templates = shopify_product_template_obj.search(
                    [('product_tmpl_id', '=', template.id)])
                if vals.get('active'):
                    shopify_templates = shopify_product_template_obj.search(
                        [('product_tmpl_id', '=', template.id), ('active', '=', False)])
                shopify_templates.write({'active': vals.get('active')})
        
        res = super(ProductTemplate, self).write(vals)

        company_instance_id = self.env.company.default_shopify_instance_id.id

        if company_instance_id:

            shopify_prepare_product_id = self.env['shopify.prepare.product.for.export.ept'].create({
                'shopify_instance_id' : company_instance_id, 
                'export_method' : "direct", 
            })

            export_data = self.env['shopify.process.import.export'].create({
                'shopify_instance_id' : company_instance_id,
                'shopify_is_set_basic_detail' : True, 
                'shopify_is_update_basic_detail' : True,
                'shopify_is_set_price' : True,
                'shopify_is_set_image' : True,
                'shopify_is_publish' : 'publish_product_global',
            })

            for product in self:
                if product.detailed_type == 'product':
                    shopify_prepare_product_id.with_context({"active_ids": [product.id], "lang": self.env.user.lang}).prepare_product_for_export()
                    shopify_product_ept_id = self.env['shopify.product.template.ept'].search([('product_tmpl_id', '=', product.id)], limit=1)
                    if not shopify_product_ept_id.exported_in_shopify: 
                        export_data.with_context({"active_ids" : [shopify_product_ept_id.id]}).manual_export_product_to_shopify()
                    else:
                        export_data.with_context({"active_ids" : [shopify_product_ept_id.id]}).manual_update_product_to_shopify()

        return res

    def update_product_data_in_shopify(self): 
        company_instance_id = self.env.company.default_shopify_instance_id.id

        shopify_prepare_product_id = self.env['shopify.prepare.product.for.export.ept'].create({
            'shopify_instance_id' : company_instance_id, 
            'export_method' : "direct", 
        })

        export_data = self.env['shopify.process.import.export'].create({
            'shopify_instance_id' : company_instance_id,
            'shopify_is_set_basic_detail' : True, 
            'shopify_is_set_price' : True,
            'shopify_is_set_image' : True, 
            'shopify_is_publish' : 'publish_product_global',
        })

        for product in self.search([('detailed_type', '=', 'product')]):
            shopify_prepare_product_id.with_context({"active_ids": [product.id]}).prepare_product_for_export()
            shopify_product_ept_id = self.env['shopify.product.template.ept'].search([('product_tmpl_id', '=', product.id)], limit=1)
            if not shopify_product_ept_id.exported_in_shopify: 
                export_data.with_context({"active_ids" : [shopify_product_ept_id.id]}).manual_export_product_to_shopify()
            else:
                export_data.with_context({"active_ids" : [shopify_product_ept_id.id]}).manual_update_product_to_shopify()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        """
        This method use to archive/unarchive shopify product base on odoo product.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 30/03/2019.
        """
        if 'active' in vals.keys():
            shopify_product_product_obj = self.env['shopify.product.product.ept']
            for product in self:
                shopify_product = shopify_product_product_obj.search(
                    [('product_id', '=', product.id)])
                if vals.get('active'):
                    shopify_product = shopify_product_product_obj.search(
                        [('product_id', '=', product.id), ('active', '=', False)])
                shopify_product.write({'active': vals.get('active')})
        res = super(ProductProduct, self).write(vals)
        return res
