# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
from lxml import etree
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model): 
    _inherit = 'product.template'

    margin_ids = fields.One2many('product.margin', 'product_tmpl_id')
    additional_cost_ids = fields.One2many('additional.cost', 'product_tmpl_id')

    list_price = fields.Float(compute="_compute_price")

    replacement_cost = fields.Float(compute="_compute_replacement_cost")
    
    total_additional_cost = fields.Float(compute="_compute_total_addional_cost")

    ingredients = fields.Text('Ingredients')
    brand = fields.Many2one('brand', 'Brand*')

    product_status = fields.Integer()  

    company_ids = fields.Many2many('res.company', string="Companies")

    product_collection_ids = fields.Many2many('shopify.product.collection', string="Collections")
    
    product_prices_ids = fields.One2many('product.prices', 'product_tmpl_id')
    
    first_product_pricelist_id = fields.Many2one('product.pricelist', '1. Lista de Precios')
    first_product_price = fields.Char('Precio', readonly="1", store=True, compute='_compute_first_product_pricelist')
    
    second_product_pricelist_id = fields.Many2one('product.pricelist', '2. Lista de Precios')
    second_product_price = fields.Char('Precio', readonly="1", store=True, compute='_compute_second_product_pricelist')
    
    third_product_pricelist_id = fields.Many2one('product.pricelist', '3. Lista de Precios')
    third_product_price = fields.Char('Precio', readonly="1", store=True, compute='_compute_third_product_pricelist')
    
    @api.depends('first_product_pricelist_id', 'first_product_pricelist_id.item_ids')
    def _compute_first_product_pricelist(self): 
        for record in self: 
            if record.first_product_pricelist_id: 
                price_with_tax = record.taxes_id.compute_all(float(record.first_product_pricelist_id.get_product_price(record.product_variant_id, 1.0, partner=False, uom_id=record.product_variant_id.uom_id.id)), product=record, partner=self.env['res.partner'])
                record.first_product_price = str(record.first_product_pricelist_id.get_product_price(record.product_variant_id, 1.0, partner=False, uom_id=record.product_variant_id.uom_id.id)) + " (" + str(float(price_with_tax['total_included'])) + " con impuestos)"
        
    @api.depends('second_product_pricelist_id', 'second_product_pricelist_id.item_ids')
    def _compute_second_product_pricelist(self): 
        for record in self:
            if record.second_product_pricelist_id:  
                price_with_tax = record.taxes_id.compute_all(float(record.second_product_pricelist_id.get_product_price(record.product_variant_id, 1.0, partner=False, uom_id=record.product_variant_id.uom_id.id)), product=record, partner=self.env['res.partner'])
                record.second_product_price = str(record.second_product_pricelist_id.get_product_price(record.product_variant_id, 1.0, partner=False, uom_id=record.product_variant_id.uom_id.id)) + " (" + str(float(price_with_tax['total_included'])) + " con impuestos)"
        
    @api.depends('third_product_pricelist_id', 'third_product_pricelist_id.item_ids')
    def _compute_third_product_pricelist(self): 
        for record in self:    
            if record.third_product_pricelist_id:
                price_with_tax = record.taxes_id.compute_all(float(record.third_product_pricelist_id.get_product_price(record.product_variant_id, 1.0, partner=False, uom_id=record.product_variant_id.uom_id.id)), product=record, partner=self.env['res.partner'])
                record.third_product_price = str(record.third_product_pricelist_id.get_product_price(record.product_variant_id, 1.0, partner=False, uom_id=record.product_variant_id.uom_id.id)) + " (" + str(float(price_with_tax['total_included'])) + " con impuestos)"


    @api.depends('margin_ids', 'replacement_cost')
    def _compute_price(self): 
        for record in self:
            record.list_price = 1.0
            margin = self.env['product.margin'].search([('product_tmpl_id', '=', record.id)], order='create_date desc', limit=1).margin
            if margin and record.replacement_cost:   
                record.list_price = record.replacement_cost / (1 - margin)


    @api.depends('seller_ids', 'bom_ids', 'additional_cost_ids')
    def _compute_replacement_cost(self): 
        for record in self: 
            has_mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', record.id), ('product_id', '=', False)], order='write_date desc', limit=1)

            
            if not has_mrp_bom: 
                vendor_pricelist = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', record.id)], order='create_date desc', limit=1)
                if vendor_pricelist and vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                    price = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
                else: 
                    price = vendor_pricelist.price
                record.replacement_cost = price
            elif has_mrp_bom: 
                record.replacement_cost = has_mrp_bom.replacement_cost_total
                
            costs = self.env['additional.cost'].search([('product_tmpl_id', '=', record.id)])
            if costs:
                for cost in costs: 
                    record.replacement_cost += cost.cost
                
    @api.depends('additional_cost_ids.cost')
    def _compute_total_addional_cost(self): 
        for product in self: 
            total = 0 
            for cost_id in product.additional_cost_ids: 
                total += cost_id.cost
                
            product.total_additional_cost = total


    @api.model
    def create(self, vals_list): 
        res = super(ProductTemplate, self).create(vals_list)

        if not res.default_code: 
            res.default_code = 'OD{}'.format(str(res.id))

        self.env['product.margin'].create(
            {
                'margin' : self.env.company.default_company_margin,
                'product_tmpl_id' : res.id,
            }
        )
        
        return res

    
    def assign_product_margin(self): 
        return {
            'view_mode' : 'form', 
            'type' : 'ir.actions.act_window', 
            'res_model' : 'assign.margin.to.product', 
            'target' : 'new', 
            'view_id' : self.env.ref('saborati.assign_margin_to_product_view').id,
            'context' : {'ids' : self.env.context.get('active_ids', [])}
        }
        
    def assign_product_collection(self): 
        return {
            'view_mode' : 'form', 
            'type'      : 'ir.actions.act_window', 
            'res_model' : 'assign.collection.to.product',
            'target'    : 'new', 
            'view_id'   : self.env.ref('saborati.assign_collection_to_product_view').id,
            'context'   : {'ids' : self.env.context.get('active_ids', [])}
        }

