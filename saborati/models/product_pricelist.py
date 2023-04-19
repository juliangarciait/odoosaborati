# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging 
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model): 
    _inherit = 'product.pricelist.item'

    base = fields.Selection([('list_price', 'Sales Price'), ('replacement_cost', 'Replacement Cost'), ('pricelist', 'Other Pricelist')])

    replacement_cost = fields.Char('Costo de reposición', compute="_compute_replacement_cost")
    
    @api.depends('applied_on', 'product_id.replacement_cost')
    def _compute_replacement_cost(self):
        for item in self: 
            if item.applied_on == '1_product': 
                item.replacement_cost = str(item.product_tmpl_id.replacement_cost)
            elif item.applied_on == '0_product_variant': 
                item.replacement_cost = str(self._get_replacement_cost(item.product_id))
            else: 
                item.replacement_cost = 'No aplica'
                
    def _get_replacement_cost(self, product): 
        replacement_cost = 0.0
        has_mrp_bom = self.env['mrp.bom'].search([('product_id', '=', product.id), ('company_id', '=', self.env.company.id)], order='write_date desc', limit=1)

        if product.product_tmpl_id.product_variant_id.id == product.id:
            if not has_mrp_bom:
                replacement_cost = product.product_tmpl_id.replacement_cost
            else:
                replacement_cost = has_mrp_bom.replacement_cost_total
        else: 
            if not has_mrp_bom: 
                vendor_pricelist = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product.product_tmpl_id.id), ('company_id', '=', self.env.company.id)], order='create_date desc', limit=1)
                if vendor_pricelist and vendor_pricelist.currency_id.id != self.env.company.currency_id.id: 
                    price = vendor_pricelist.currency_id._convert(vendor_pricelist.price, self.env.company.currency_id, self.env.company, vendor_pricelist.create_date)
                else: 
                    price = vendor_pricelist.price
                replacement_cost = price
            elif has_mrp_bom: 
                replacement_cost = has_mrp_bom.replacement_cost_total
                
        return replacement_cost