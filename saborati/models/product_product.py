# -*- coding: utf-8 -*-

from odoo import models, api, _, fields
from odoo.exceptions import ValidationError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model): 
    _inherit = 'product.product'

    @api.depends_context('force_company')
    def _compute_replacement_cost_new(self):
        self = self.sudo()
        order = "id"
        product_template = self[0].product_tmpl_id
        if product_template:
            variant = product_template.product_variant_id
            if variant.bom_count == 0:
                order = "default_code"
            else:
                has_mrp_bom = variant.bom_ids.filtered(lambda bom: bom.product_id.id == variant.id and bom.company_id.id == self.env.company.id).sorted('write_date', True)
                if has_mrp_bom:
                    if not product_template.product_variant_ids.ids in [line.product_id.id for line in has_mrp_bom.bom_line_ids]:
                        order = "default_code"
                order = "bom_count"
            
        for record in self.sorted(order):
            new_replace_cost = 0.0
            record = record.sudo()
            has_mrp_bom = record.bom_ids.filtered(lambda bom: bom.product_id.id == record.id and bom.company_id.id == self.env.company.id).sorted('write_date', True)
            
            if len(has_mrp_bom) > 0:
                for line in has_mrp_bom.bom_line_ids:
                    new_replace_cost += line.product_id.replacement_cost * line.product_qty
            else:
                new_replace_cost = record.product_tmpl_id.product_variant_id.replacement_cost
                if record.product_tmpl_id.product_variant_id.id == record.id:
                    vendor_pricelist = self.env['product.supplierinfo'].search(
                        [('product_tmpl_id', '=', record.product_tmpl_id.id),
                         ('company_id', '=', self.env.company.id)], order='create_date desc', limit=1)
                    stock_move = self.env['stock.move'].search(
                        [('state', '=', 'done'),
                         ('product_id', '=', record.id),
                         ('company_id', '=', self.env.company.id),
                         ('picking_type_id', 'in', [1, 40, 10, 19, 32])], order="write_date desc", limit=1)
                    if stock_move and vendor_pricelist: 
                        vendor_date = datetime.strptime(str(vendor_pricelist.write_date), '%Y-%m-%d %H:%M:%S.%f')
                        stock_move_date = datetime.strptime(str(stock_move.write_date), '%Y-%m-%d %H:%M:%S.%f')
                        if stock_move_date > vendor_date:
                            new_replace_cost = stock_move.purchase_line_id.price_unit
                        else:
                            if vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                                new_replace_cost = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
                            else: 
                                new_replace_cost = vendor_pricelist.price
                    elif vendor_pricelist and not stock_move:
                        if vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                            new_replace_cost = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
                        else: 
                            new_replace_cost = vendor_pricelist.price
                    elif not vendor_pricelist and stock_move:
                        new_replace_cost = stock_move.purchase_line_id.price_unit
                    extra_costs = self.env['additional.cost'].search([('product_tmpl_id', '=', record.product_tmpl_id.id)])
                    for cost in extra_costs: 
                        new_replace_cost += cost.cost
                else:
                    new_replace_cost = record.calculate_if_not_mrp_bom(record)
            record.replacement_cost = new_replace_cost

    
    list_price = fields.Float(compute="_compute_price")
    
    replacement_cost = fields.Float(compute="_compute_replacement_cost_new")
    # new_replacement_cost = fields.Float(compute="_compute_replacement_cost_new")#, store=True)
    
    purchase_ok = fields.Boolean('Can be Purchased', default=True)
    sale_ok = fields.Boolean('Can be Sold', default=True)
    
    product_prices_ids = fields.One2many('product.product.prices', 'product_id')
    
    available_quantity = fields.Float(compute='_search_available_quantity', string="Cantidad disponible")
    
    is_kit = fields.Boolean(compute="_compute_if_kit", store=True)
    
    @api.depends('bom_ids', 'bom_ids.type', 'bom_ids.bom_line_ids')
    def _compute_if_kit(self): 
        for rec in self: 
            kit = self.env['mrp.bom'].search([('type', '=', 'phantom'), ('company_id', '=', self.env.company.id), ('product_id', '=', rec.id)], order='write_date desc', limit=1)
            if kit: 
                rec.is_kit = True
            else: 
                rec.is_kit = False
    
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
        
    
    @api.depends('seller_ids', 'bom_ids', 'bom_ids.bom_line_ids')
    def _compute_replacement_cost(self): 
        self.flush()
        for record in self:
            record.replacement_cost = 0.0
            has_mrp_bom = self.env['mrp.bom'].search([('product_id', '=', record.id), ('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)
            if record.product_tmpl_id.product_variant_id.id == record.id:
                if not has_mrp_bom:
                    record.replacement_cost = record.product_tmpl_id.replacement_cost if record.type != 'product' else self.calculate_if_not_mrp_bom(record)
                else:
                    record.replacement_cost = has_mrp_bom.replacement_cost_total
            else: 
                if not has_mrp_bom: 
                    record.replacement_cost = self.calculate_if_not_mrp_bom(record)
                elif has_mrp_bom: 
                    record.replacement_cost = has_mrp_bom.replacement_cost_total
                    
            if record.product_tmpl_id.product_variant_id.id == record.id:       
                costs = self.env['additional.cost'].search([('product_tmpl_id', '=', record.product_tmpl_id.id)])
                if costs:
                    for cost in costs: 
                        record.replacement_cost += cost.cost
            
    def calculate_if_not_mrp_bom(self, product):
        cost = 0.0
        vendor_pricelist = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product.product_tmpl_id.id), ('company_id', '=', self.env.company.id)], order='create_date desc', limit=1)
        stock_move = self.env['stock.move'].search([('state', '=', 'done'), ('product_id', '=', product.id), ('company_id', '=', self.env.company.id), ('picking_type_id', 'in', [1, 40, 10, 19, 32])], order="write_date desc", limit=1)
        #po_price = self.env['purchase.order.line'].search([('state', '=', 'purchase'), ('product_id', '=', product.id), ('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)

        if stock_move and vendor_pricelist: 
            vendor_date = datetime.strptime(str(vendor_pricelist.write_date), '%Y-%m-%d %H:%M:%S.%f')
            stock_move_date = datetime.strptime(str(stock_move.write_date), '%Y-%m-%d %H:%M:%S.%f')
            if stock_move_date > vendor_date: 
                cost = stock_move.purchase_line_id.price_unit 
            else: 
                if vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                    cost = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
                else: 
                    cost = vendor_pricelist.price
        elif vendor_pricelist and not stock_move:
            if vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                cost = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
            else: 
                cost = vendor_pricelist.price
        elif not vendor_pricelist and stock_move:
            cost = stock_move.purchase_line_id.price_unit
            
        return cost
            
    @api.depends('margin_ids', 'replacement_cost')
    def _compute_price(self): 
        for record in self:
            record.list_price = 1.0
            _logger.info("$"*900)
            _logger.info(record.id)
            _logger.info(record.replacement_cost)
            _logger.info(record.with_company(self.company_id).replacement_cost)
            margin = self.env['product.margin'].search([('product_tmpl_id', '=', record.product_tmpl_id.id), ('company_id', '=', self.env.company.id)], order='create_date desc', limit=1).margin
            _logger.info(margin)
            if margin and record.with_company(self.company_id).replacement_cost:
                record.list_price = record.with_company(self.company_id).replacement_cost / (1 - margin)
