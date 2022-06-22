# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 


class PurchaseOrder(models.Model): 
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()

        for purchase in self: 
            has_mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', purchase.product_id.product_tmpl_id.id)])
            if not has_mrp_bom:
                for line in purchase.order_line: 
                    line.product_id.product_tmpl_id.replacement_cost = line.price_unit

        return res