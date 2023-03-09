# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
from odoo.exceptions import ValidationError
import logging 
_logger = logging.getLogger(__name__)


class MrpBom(models.Model): 
    _inherit = 'mrp.bom'

    @api.model
    def create(self, values):
        bill = super(MrpBom, self).create(values)

        total = 0 
        for bom_line in bill.bom_line_ids: 
            total += bom_line.product_id.replacement_cost * bom_line.product_qty

        if bill.product_tmpl_id: 
            bill.product_tmpl_id.replacement_cost = total
            
        if bill.product_id: 
            bill.product_id.replacement_cost = total

        return bill

    def write(self, vals): 
        res = super(MrpBom, self).write(vals)

        for bill in self: 
            total = 0
            for bom_line in bill.bom_line_ids: 
                total += bom_line.product_id.replacement_cost * bom_line.product_qty

            if bill.product_tmpl_id:
                bill.product_tmpl_id.replacement_cost = total
            
            if bill.product_id: 
                bill.product_id.replacement_cost = total

        return res     


class MrpBomLine(models.Model): 
    _inherit = 'mrp.bom.line'


    replacement_cost = fields.Float('Replacement Cost', compute="_compute_replacement_cost")
    
    @api.depends('product_id.replacement_cost')
    def _compute_replacement_cost(self): 
        for record in self: 
            record.replacement_cost = record.product_id.replacement_cost
