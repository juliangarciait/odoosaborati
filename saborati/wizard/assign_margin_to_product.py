# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 


class AssignMarginToProduct(models.Model): 
    _name = 'assign.margin.to.product'

    margin = fields.Float(string="Margen")


    def apply(self): 
        product_ids = self.env['product.template'].search([('id', 'in', self._context['ids'])])

        for product in product_ids: 
            self.env['product.margin'].create(
            {
                'margin' : self.margin,
                'product_tmpl_id' : product.id,
            }
        )