# -*- coding: utf-8 -*-

from odoo import models, api, _, fields
from odoo.exceptions import ValidationError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model): 
    _inherit = 'product.product'
    
    list_price = fields.Float(compute="_compute_price")
    
    replacement_cost = fields.Float(compute="_compute_replacement_cost")
    
    purchase_ok = fields.Boolean('Can be Purchased', default=True)
    sale_ok = fields.Boolean('Can be Sold', default=True)
    
    product_prices_ids = fields.One2many('product.product.prices', 'product_id')
    
    available_quantity = fields.Float(compute='_search_available_quantity', string="Cantidad disponible")
    
    @api.depends('stock_quant_ids.available_quantity')
    def _search_available_quantity(self): 
        for product in self: 
            qty = 0
            is_kit = self.env['mrp.bom'].search([('product_id', '=', product.id), ('type', '=', 'phantom')])
            if not is_kit: 
                qty = self._get_product_available_quantity(product)
            else:
                qty_bom = 0 
                qty_quant = 0 
                for line in is_kit.bom_line_ids: 
                    if line.product_id.detailed_type == 'product': 
                        qty_bom += line.product_qty
                        
                
                
                        
                        
                        
            product.available_quantity = float(qty)
            

    def _get_product_available_quantity(self, product): 
        qty = 0 
        stock_quants = self.env['stock.quant'].search([('product_id', '=', product.id)])
        for quant in stock_quants:
            if quant.inventory_date: 
                qty += quant.available_quantity
                
        return qty
        
    
    @api.depends('seller_ids', 'bom_ids')
    def _compute_replacement_cost(self): 
        for record in self:
            record.replacement_cost = 0.0
            has_mrp_bom = self.env['mrp.bom'].search([('product_id', '=', record.id), ('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)

            #if record.product_tmpl_id.product_variant_id.id == record.id:
            #    if not has_mrp_bom:
            #        record.replacement_cost = record.product_tmpl_id.replacement_cost
            #    else:
            #        record.replacement_cost = has_mrp_bom.replacement_cost_total
            #else: 
            if not has_mrp_bom: 
                price = 0.0
                vendor_pricelist = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', record.product_tmpl_id.id), ('company_id', '=', self.env.company.id)], order='create_date desc', limit=1)
                po_price = self.env['purchase.order.line'].search([('state', '=', 'purchase'), ('product_id', '=', record.id), ('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)
                vendor_date = datetime.strptime(str(vendor_pricelist.write_date), '%Y-%m-%d %H:%M:%S.%f')
                po_date = datetime.strptime(str(po_price.write_date), '%Y-%m-%d %H:%M:%S.%f')
                if po_price and vendor_pricelist: 
                    if po_date > vendor_date: 
                        price = po_price.price_unit 
                    else: 
                        if vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                            price = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
                        else: 
                            price = vendor_pricelist.price
                elif vendor_pricelist and not po_price:
                    if vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                        price = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
                    else: 
                        price = vendor_pricelist.price
                elif not vendor_pricelist and po_price:
                    price = po_price.price_unit 
                    
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
            margin = self.env['product.margin'].search([('product_tmpl_id', '=', record.product_tmpl_id.id), ('company_id', '=', self.env.company.id)], order='create_date desc', limit=1).margin
            if margin and record.replacement_cost:
                record.list_price = record.replacement_cost / (1 - margin)
