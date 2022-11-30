# -*- coding: utf-8 -*-

from odoo import models, api, _, fields

import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model): 
    _inherit = 'product.product'
    
    list_price = fields.Float(compute="_compute_price")
    
    replacement_cost = fields.Float(compute="_compute_replacement_cost")
    
    @api.depends('seller_ids', 'bom_ids')
    def _compute_replacement_cost(self): 
        for record in self: 
            record.replacement_cost = 0.0
            has_mrp_bom = self.env['mrp.bom'].search([('product_id', '=', record.id)], order='write_date desc', limit=1)
            if not has_mrp_bom: 
                vendor_pricelist = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', record.id)], order='create_date desc', limit=1)
                if vendor_pricelist and vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                    price = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
                else: 
                    price = vendor_pricelist.price
                record.replacement_cost = price
            elif has_mrp_bom: 
                record.replacement_cost = has_mrp_bom.replacement_cost_total
                
            #costs = self.env['additional.cost'].search([('product_tmpl_id', '=', record.id)])
            #if costs:
            #    for cost in costs: 
            #        record.replacement_cost += cost.cost
            
    @api.depends('margin_ids', 'replacement_cost')
    def _compute_price(self): 
        for record in self:
            record.list_price = 1.0
            margin = self.env['product.margin'].search([('product_tmpl_id', '=', record.product_tmpl_id.id)], order='create_date desc', limit=1).margin
            if margin and record.replacement_cost:   
                record.list_price = record.replacement_cost / (1 - margin)
