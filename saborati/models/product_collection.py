# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 
import logging 
_logger = logging.getLogger(__name__)


class ProductCollection(models.Model): 
    _name = 'product.collection'

    name = fields.Char()
    body_html = fields.Html()
    is_exported = fields.Boolean()
    company_ids = fields.Many2many('res.company', string="Companies")
    shopify_product_collection_ids = fields.One2many('shopify.product.collection', 'collection_id', string="Shopify Product Collection")

    
    #product_ids = fields.Many2many('product.template', string="Products")
    #shopify_collection_id = fields.Char("Shopify Collection ID")
    
class ShopifyProductCollection(models.Model): 
    _name = 'shopify.product.collection'
    
    name = fields.Char()
    body_html = fields.Html()
    is_exported = fields.Boolean()

    company_id = fields.Many2one('res.company', string="Company")
    product_ids = fields.Many2many('product.template', string="Products")
    shopify_collection_id = fields.Char("Shopify Collection ID")
    
    collection_id = fields.Many2one('product.collection', company_dependent=True)
    