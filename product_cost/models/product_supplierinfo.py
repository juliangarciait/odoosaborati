# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 
from odoo.exceptions import ValidationError
import logging 
_logger = logging.getLogger(__name__)


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.model
    def create(self, vals_list): 
        res = super(ProductSupplierinfo, self).create(vals_list)
        
        has_mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', res.product_tmpl_id.id)])
        if not has_mrp_bom: 
            res.product_tmpl_id.replacement_cost = res.price

        return res

    def write(self, vals):
        res = super(ProductSupplierinfo, self).write(vals)
        
        for vendor_pricelist in self:
            has_mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', vendor_pricelist.product_tmpl_id.id)])
            if not has_mrp_bom: 
                vendor_pricelist.product_tmpl_id.replacement_cost = vendor_pricelist.price

        return res