# -*- coding: utf-8 -*-

from odoo import fields, api, _, models

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    product_ids = fields.Many2many('product.product', compute="_get_products")
    
    @api.depends('order_id.partner_id')
    def _get_products(self): 
        for line in self: 
            ids = []
            vendors = self.env['product.supplierinfo'].search([('name', '=', line.order_id.partner_id.id)])
            for vendor in vendors:  
                product = self.env['product.template'].search([('id', '=', vendor.product_tmpl_id.id)])
                for variant in product.product_variant_ids.ids: 
                    ids.append(variant)
                
            line.product_ids = ids
            line.product_ids = line.product_ids._origin
