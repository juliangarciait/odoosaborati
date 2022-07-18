# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductCategory(models.Model): 
    _inherit = 'product.category'

    product_ids = fields.One2many('product.template', 'categ_id')