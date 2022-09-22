# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError
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

                    
class ProductProduct(models.Model):
    _inherit = 'product.product'

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
        return res
