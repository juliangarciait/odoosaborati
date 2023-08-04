# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
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
    # replacement_cost = fields.Float(related="product_variant_id.replacement_cost")
    
    total_additional_cost = fields.Float(compute="_compute_total_addional_cost")

    ingredients = fields.Text('Ingredients')
    brand = fields.Many2one('brand', 'Brand*')

    product_status = fields.Integer()  

    company_ids = fields.Many2many('res.company', string="Companies")

    product_collection_ids = fields.Many2many('shopify.product.collection', string="Collections")
    
    product_prices_ids = fields.One2many('product.prices', 'product_tmpl_id')
    
    weight_for_variants = fields.Float(default=0.0, compute="_get_weight", store=True)
    
    @api.depends('weight')
    def _get_weight(self): 
        for product in self: 
            if product.weight != 0.0: 
                product.weight_for_variants = product.weight

    @api.depends('margin_ids', 'replacement_cost')
    def _compute_price(self): 
        for record in self:
            record.list_price = 1.0
            margin = self.env['product.margin'].search([('product_tmpl_id', '=', record.id), ('company_id', '=', self.env.company.id)], order='create_date desc', limit=1).margin
            if margin and record.replacement_cost:   
                record.list_price = record.replacement_cost / (1 - margin)

    @api.depends_context('force_company')
    def _compute_replacement_cost(self): 
        for record in self: 
            replacement_cost = 0
            if record.product_variant_id.bom_count >= 0:
                variant_bom = record.product_variant_ids.filtered(lambda v: v.bom_count == 0)
                replacement_cost = variant_bom and variant_bom[0].replacement_cost
            else:
                replacement_cost = record.product_variant_id.replacement_cost
            record.replacement_cost = replacement_cost
                
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

        if len(res.product_variant_ids.ids) == 1 and res.product_variant_ids.ids[0] == res.product_variant_id.id: 
            if res.detailed_type == 'product' and res.weight <= 0.0 and res.sale_ok:
                raise ValidationError (_('El peso tiene un valor de 0.0. Coloque un valor válido'))
        else: 
            for variant in res.product_variant_ids: 
                if res.weight_for_variants != 0.0:
                    variant.weight = res.weight_for_variants
                
        self.env['product.margin'].create(
            {
                'margin' : self.env.company.default_company_margin,
                'product_tmpl_id' : res.id,
            }
        )
        
        return res
    
    def write(self, vals): 
        res = super(ProductTemplate, self).write(vals)
        
        for product in self:                
            if len(product.product_variant_ids.ids) == 1 and product.product_variant_ids.ids[0] == product.product_variant_id.id: 
                if product.detailed_type == 'product' and product.weight <= 0.0 and product.sale_ok:
                    raise ValidationError (_('El peso tiene un valor de 0.0. Coloque un valor válido'))
            else: 
                for variant in product.product_variant_ids: 
                    if product.weight_for_variants != 0.0:
                        variant.weight = product.weight_for_variants
                    
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

