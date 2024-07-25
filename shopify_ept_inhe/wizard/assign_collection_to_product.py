# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AssignCollectionToProduct(models.TransientModel): 
    _name = 'assign.collection.to.product'
    
    collection_ids = fields.Many2many('shopify.product.collection')
    
    def apply(self): 
        product_ids = self.env['product.template'].search([('id', 'in', self._context['ids'])])
        
        for product in product_ids: 
            for collection in self.collection_ids: 
                product.write({
                    'product_collection_ids' : [(4, collection.id)]
                })