# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
from odoo.exceptions import ValidationError


class ChangeProductStatus(models.TransientModel): 
    _name = 'change.product.status'


    product_status = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('archived', 'Archived')], string="Product status")


    def apply(self): 
        product_ids = self.env['shopify.product.template.ept'].search([('id', 'in', self._context['ids'])])

        for product in product_ids: 
            if not product.product_tmpl_id.product_general_status and self.product_status == 'active': 
                product.product_status = 'draft'
                raise ValidationError('La plantilla original de {} tiene desmarcado Product General Status; por lo tanto, no se puede cambiar el estatus del producto'.format(product.product_tmpl_id.name))
            else: 
                product.product_status = self.product_status
                export_data = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                    'shopify_is_set_basic_detail' : True,
                    'shopify_is_update_basic_detail' : True,
                    'shopify_is_set_price' : True,
                    'shopify_is_set_image' : True,
                    'shopify_is_publish' : 'publish_product_global',
                })
                export_data.with_context({"active_ids" : [product.id]}).manual_update_product_to_shopify()

