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
            total += bom_line.product_id.product_tmpl_id.replacement_cost * bom_line.product_qty

        bill.product_tmpl_id.replacement_cost = total

        return bill

    def write(self, vals): 
        res = super(MrpBom, self).write(vals)

        for bill in self: 
            total = 0
            for bom_line in bill.bom_line_ids: 
                total += bom_line.product_id.product_tmpl_id.replacement_cost * bom_line.product_qty

            bill.product_tmpl_id.replacement_cost = total

        return res     


class MrpBomLine(models.Model): 
    _inherit = 'mrp.bom.line'


    replacement_cost = fields.Float('Replacement Cost', related='product_id.product_tmpl_id.replacement_cost')
