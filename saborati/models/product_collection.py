# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 


class ProductCollection(models.Model): 
    _name = 'product.collection'

    name = fields.Char()
    body_html = fields.Html()
    is_exported = fields.Boolean()

    product_ids = fields.Many2many('product.template', string="Products")