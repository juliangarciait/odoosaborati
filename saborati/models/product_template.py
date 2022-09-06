# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
from lxml import etree
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model): 
    _inherit = 'product.template'

    margin_ids = fields.One2many('product.margin', 'product_tmpl_id')

    list_price = fields.Float(compute="_compute_price")

    replacement_cost = fields.Float(compute="_compute_replacement_cost")

    ingredients = fields.Text('Ingredients')
    brand = fields.Many2one('brand', 'Brand*')

    product_general_status = fields.Boolean(default=True, company_dependent=True)
    product_status = fields.Integer()  

    company_ids = fields.Many2many('res.company', string="Companies")

    @api.depends('margin_ids', 'replacement_cost')
    def _compute_price(self): 
        for record in self:
            record.list_price = 1.0
            margin = self.env['product.margin'].search([('product_tmpl_id', '=', record.id)], order='create_date desc', limit=1).margin
            if margin and record.replacement_cost:   
                record.list_price = record.replacement_cost / (1 - margin)


    @api.depends('seller_ids', 'bom_ids')
    def _compute_replacement_cost(self): 
        for record in self: 
            record.replacement_cost = 0.0
            has_mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', record.id)], order='write_date desc', limit=1)
            if not has_mrp_bom: 
                record.replacement_cost = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', record.id)], order='create_date desc', limit=1).price
            elif has_mrp_bom: 
                record.replacement_cost = has_mrp_bom.replacement_cost_total


    @api.model
    def create(self, vals_list): 
        res = super(ProductTemplate, self).create(vals_list)


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


                


    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductTemplate, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                            toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field[@name='company_id']")
            node = nodes[0] if nodes else False
            node.set('readonly', '1')
            res['arch'] = etree.tostring(doc)
        return res
