# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 

class ProductTags(models.Model): 
    _name = 'product.tags'

    name = fields.Char(string="Tag name")
    color = fields.Integer(string="Tag color")