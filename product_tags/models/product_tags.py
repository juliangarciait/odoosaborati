# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 

class ProductTags(models.Model): 
    _name = 'product.tags'

    name = fields.Char(string="Tag name")
    color = fields.Integer(string="Tag color")
    to_shopify = fields.Boolean(string="Export to Shopify?")

    product_ids = fields.Many2many('product.template', column1='tag_id', column2='product_id', string="Products")