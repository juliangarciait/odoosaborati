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
                if vendor.product_id: 
                    ids.append(vendor.product_id.id)
                elif vendor.product_tmpl_id: 
                    product = self.env['product.product'].search([('id', '=', vendor.product_tmpl_id.product_variant_id.id)])
                    ids.append(product.id)
            line.product_ids = ids
            line.product_ids = line.product_ids._origin
    